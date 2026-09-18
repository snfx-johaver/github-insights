"""Config flow for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    GitHubAuthenticationError,
    GitHubClient,
    GitHubConnectionError,
    GitHubInsightsError,
    GitHubInvalidServerError,
)
from .const import (
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LOGIN,
    CONF_AUTO_DISCOVER,
    CONF_ORGANIZATIONS,
    CONF_REPOSITORIES,
    CONF_SERVER,
    CONF_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_AUTO_DISCOVER,
    DEFAULT_SERVER,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_UPDATE_INTERVAL_MINUTES,
)
from .coordinator import GitHubInsightsConfigEntry
from .models import GitHubSnapshot


@dataclass(slots=True)
class ValidatedSetup:
    """Validated setup values retained between flow steps."""

    server: str
    token: str
    snapshot: GitHubSnapshot


async def async_validate_input(
    hass: HomeAssistant, server: str, token: str
) -> ValidatedSetup:
    """Validate a server and token without storing credentials elsewhere."""
    client = GitHubClient(async_get_clientsession(hass), token, server)
    snapshot = await client.async_fetch_snapshot()
    return ValidatedSetup(
        server=client.server.web_url,
        token=token,
        snapshot=snapshot,
    )


class GitHubInsightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a GitHub Insights config flow."""

    VERSION = 2
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._validated: ValidatedSetup | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect and validate a GitHub server and token."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._validated = await async_validate_input(
                    self.hass,
                    user_input[CONF_SERVER],
                    user_input[CONF_TOKEN],
                )
            except GitHubInvalidServerError:
                errors["base"] = "invalid_server"
            except GitHubAuthenticationError:
                errors["base"] = "invalid_auth"
            except GitHubConnectionError:
                errors["base"] = "cannot_connect"
            except GitHubInsightsError:
                errors["base"] = "unknown"
            else:
                return await self.async_step_scope()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERVER, default=DEFAULT_SERVER): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.URL)
                    ),
                    vol.Required(CONF_TOKEN): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_scope(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select organizations and repositories discovered during validation."""
        if self._validated is None:
            return self.async_abort(reason="invalid_auth")

        snapshot = self._validated.snapshot
        if user_input is not None:
            await self.async_set_unique_id(
                f"{self._validated.server}:{snapshot.account.id}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=snapshot.account.login,
                data={
                    CONF_SERVER: self._validated.server,
                    CONF_TOKEN: self._validated.token,
                    CONF_ACCOUNT_ID: snapshot.account.id,
                    CONF_ACCOUNT_LOGIN: snapshot.account.login,
                },
                options={
                    CONF_AUTO_DISCOVER: user_input[CONF_AUTO_DISCOVER],
                    CONF_ORGANIZATIONS: user_input[CONF_ORGANIZATIONS],
                    CONF_REPOSITORIES: user_input[CONF_REPOSITORIES],
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_MINUTES,
                },
            )

        return self.async_show_form(
            step_id="scope",
            data_schema=_scope_schema(
                [organization.login for organization in snapshot.organizations],
                [repository.full_name for repository in snapshot.repositories],
            ),
            description_placeholders={
                "account": snapshot.account.login,
                "repository_count": str(len(snapshot.repositories)),
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Start reauthentication."""
        self._validated = None
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Replace an expired token after verifying the same account."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                validated = await async_validate_input(
                    self.hass,
                    entry.data[CONF_SERVER],
                    user_input[CONF_TOKEN],
                )
            except GitHubAuthenticationError:
                errors["base"] = "invalid_auth"
            except GitHubConnectionError:
                errors["base"] = "cannot_connect"
            except GitHubInsightsError:
                errors["base"] = "unknown"
            else:
                if validated.snapshot.account.id != entry.data[CONF_ACCOUNT_ID]:
                    errors["base"] = "wrong_account"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={CONF_TOKEN: validated.token},
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: GitHubInsightsConfigEntry,
    ) -> GitHubInsightsOptionsFlow:
        """Return the options flow."""
        return GitHubInsightsOptionsFlow(config_entry)


class GitHubInsightsOptionsFlow(config_entries.OptionsFlow):
    """Manage GitHub Insights options."""

    def __init__(self, entry: GitHubInsightsConfigEntry) -> None:
        """Initialize options."""
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update repository selection and polling interval."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        runtime = self._entry.runtime_data
        snapshot = runtime.coordinator.data if runtime is not None else None
        organizations = (
            [organization.login for organization in snapshot.organizations]
            if snapshot
            else list(self._entry.options.get(CONF_ORGANIZATIONS, []))
        )
        repositories = (
            [repository.full_name for repository in snapshot.repositories]
            if snapshot
            else list(self._entry.options.get(CONF_REPOSITORIES, []))
        )
        schema = _scope_schema(
            organizations,
            repositories,
            defaults=self._entry.options,
        ).extend(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self._entry.options.get(
                        CONF_UPDATE_INTERVAL,
                        DEFAULT_UPDATE_INTERVAL_MINUTES,
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_UPDATE_INTERVAL_MINUTES,
                        max=MAX_UPDATE_INTERVAL_MINUTES,
                        step=5,
                        mode=NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


def _scope_schema(
    organizations: list[str],
    repositories: list[str],
    *,
    defaults: Mapping[str, Any] | None = None,
) -> vol.Schema:
    """Build the shared organization/repository selection schema."""
    values = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_AUTO_DISCOVER,
                default=values.get(CONF_AUTO_DISCOVER, DEFAULT_AUTO_DISCOVER),
            ): bool,
            vol.Optional(
                CONF_ORGANIZATIONS,
                default=values.get(CONF_ORGANIZATIONS, []),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=organizations,
                    multiple=True,
                    sort=True,
                )
            ),
            vol.Optional(
                CONF_REPOSITORIES,
                default=values.get(CONF_REPOSITORIES, []),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=repositories,
                    multiple=True,
                    sort=True,
                )
            ),
        }
    )

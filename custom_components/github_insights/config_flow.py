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
    CONF_BILLING_ENTERPRISE,
    CONF_BILLING_INTERVAL,
    CONF_BILLING_ORGANIZATIONS,
    CONF_BUDGET_CRITICAL_THRESHOLD,
    CONF_BUDGET_MANAGEMENT,
    CONF_BUDGET_WARNING_THRESHOLD,
    CONF_ESTIMATED_MINUTES,
    CONF_ENABLED_CATEGORIES,
    CONF_INCLUDE_ARCHIVED,
    CONF_INCLUDE_FORKS,
    CONF_MAX_REPOSITORIES,
    CONF_ORGANIZATIONS,
    CONF_PERSONAL_BILLING,
    CONF_REFERENCE_RUNNER,
    CONF_REPOSITORIES,
    CONF_SERVER,
    CONF_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_AUTO_DISCOVER,
    DEFAULT_BILLING_INTERVAL_MINUTES,
    DEFAULT_BUDGET_CRITICAL_THRESHOLD,
    DEFAULT_BUDGET_MANAGEMENT,
    DEFAULT_BUDGET_WARNING_THRESHOLD,
    DEFAULT_ESTIMATED_MINUTES,
    DEFAULT_PERSONAL_BILLING,
    DEFAULT_REFERENCE_RUNNER,
    DEFAULT_SERVER,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_BILLING_INTERVAL_MINUTES,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_BILLING_INTERVAL_MINUTES,
    DEFAULT_ENABLED_CATEGORIES,
    DEFAULT_INCLUDE_ARCHIVED,
    DEFAULT_INCLUDE_FORKS,
    DEFAULT_MAX_REPOSITORIES,
    DEFAULT_SERVER,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SELECTED_REPOSITORIES,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_SELECTED_REPOSITORIES,
    MIN_UPDATE_INTERVAL_MINUTES,
    REFERENCE_RUNNER_PRICES,
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

    VERSION = 3
    MINOR_VERSION = 2

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
                    CONF_INCLUDE_ARCHIVED: user_input[CONF_INCLUDE_ARCHIVED],
                    CONF_INCLUDE_FORKS: user_input[CONF_INCLUDE_FORKS],
                    CONF_ENABLED_CATEGORIES: user_input[CONF_ENABLED_CATEGORIES],
                    CONF_MAX_REPOSITORIES: user_input[CONF_MAX_REPOSITORIES],
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_MINUTES,
                    CONF_BILLING_INTERVAL: DEFAULT_BILLING_INTERVAL_MINUTES,
                    CONF_PERSONAL_BILLING: DEFAULT_PERSONAL_BILLING,
                    CONF_BILLING_ORGANIZATIONS: user_input[CONF_ORGANIZATIONS],
                    CONF_BILLING_ENTERPRISE: "",
                    CONF_BUDGET_MANAGEMENT: DEFAULT_BUDGET_MANAGEMENT,
                    CONF_REFERENCE_RUNNER: DEFAULT_REFERENCE_RUNNER,
                    CONF_ESTIMATED_MINUTES: DEFAULT_ESTIMATED_MINUTES,
                    CONF_BUDGET_WARNING_THRESHOLD: DEFAULT_BUDGET_WARNING_THRESHOLD,
                    CONF_BUDGET_CRITICAL_THRESHOLD: DEFAULT_BUDGET_CRITICAL_THRESHOLD,
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
                stored_account_id = entry.data.get(CONF_ACCOUNT_ID)
                stored_login = entry.data.get(CONF_ACCOUNT_LOGIN)
                if (
                    stored_account_id is not None
                    and validated.snapshot.account.id != stored_account_id
                ) or (
                    stored_account_id is None
                    and stored_login is not None
                    and validated.snapshot.account.login != stored_login
                ):
                    errors["base"] = "wrong_account"
                else:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        unique_id=(
                            f"{validated.server}:{validated.snapshot.account.id}"
                        ),
                    )
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_TOKEN: validated.token,
                            CONF_ACCOUNT_ID: validated.snapshot.account.id,
                            CONF_ACCOUNT_LOGIN: validated.snapshot.account.login,
                        },
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

        runtime = getattr(self._entry, "runtime_data", None)
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
                ),
                vol.Required(
                    CONF_BILLING_INTERVAL,
                    default=self._entry.options.get(
                        CONF_BILLING_INTERVAL,
                        DEFAULT_BILLING_INTERVAL_MINUTES,
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_BILLING_INTERVAL_MINUTES,
                        max=MAX_BILLING_INTERVAL_MINUTES,
                        step=30,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PERSONAL_BILLING,
                    default=self._entry.options.get(
                        CONF_PERSONAL_BILLING, DEFAULT_PERSONAL_BILLING
                    ),
                ): bool,
                vol.Optional(
                    CONF_BILLING_ORGANIZATIONS,
                    default=self._entry.options.get(
                        CONF_BILLING_ORGANIZATIONS, organizations
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=organizations,
                        multiple=True,
                        sort=True,
                    )
                ),
                vol.Optional(
                    CONF_BILLING_ENTERPRISE,
                    default=self._entry.options.get(CONF_BILLING_ENTERPRISE, ""),
                ): TextSelector(TextSelectorConfig()),
                vol.Required(
                    CONF_BUDGET_MANAGEMENT,
                    default=self._entry.options.get(
                        CONF_BUDGET_MANAGEMENT, DEFAULT_BUDGET_MANAGEMENT
                    ),
                ): bool,
                vol.Required(
                    CONF_REFERENCE_RUNNER,
                    default=self._entry.options.get(
                        CONF_REFERENCE_RUNNER, DEFAULT_REFERENCE_RUNNER
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(options=list(REFERENCE_RUNNER_PRICES))
                ),
                vol.Required(
                    CONF_ESTIMATED_MINUTES,
                    default=self._entry.options.get(
                        CONF_ESTIMATED_MINUTES, DEFAULT_ESTIMATED_MINUTES
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=1_000_000,
                        step=100,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_BUDGET_WARNING_THRESHOLD,
                    default=self._entry.options.get(
                        CONF_BUDGET_WARNING_THRESHOLD,
                        DEFAULT_BUDGET_WARNING_THRESHOLD,
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=100, step=1, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_BUDGET_CRITICAL_THRESHOLD,
                    default=self._entry.options.get(
                        CONF_BUDGET_CRITICAL_THRESHOLD,
                        DEFAULT_BUDGET_CRITICAL_THRESHOLD,
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=100, step=1, mode=NumberSelectorMode.BOX
                    )
                ),
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
            vol.Required(
                CONF_INCLUDE_ARCHIVED,
                default=values.get(CONF_INCLUDE_ARCHIVED, DEFAULT_INCLUDE_ARCHIVED),
            ): bool,
            vol.Required(
                CONF_INCLUDE_FORKS,
                default=values.get(CONF_INCLUDE_FORKS, DEFAULT_INCLUDE_FORKS),
            ): bool,
            vol.Required(
                CONF_ENABLED_CATEGORIES,
                default=values.get(
                    CONF_ENABLED_CATEGORIES, list(DEFAULT_ENABLED_CATEGORIES)
                ),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        "repositories",
                        "workflows",
                        "releases",
                        "activity",
                        "deployments",
                        "traffic",
                        "security",
                        "copilot",
                    ],
                    multiple=True,
                    sort=True,
                )
            ),
            vol.Required(
                CONF_MAX_REPOSITORIES,
                default=values.get(CONF_MAX_REPOSITORIES, DEFAULT_MAX_REPOSITORIES),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SELECTED_REPOSITORIES,
                    max=MAX_SELECTED_REPOSITORIES,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
    )

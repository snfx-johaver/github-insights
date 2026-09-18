# Contributing

GitHub Insights is in its architecture phase. Contributions should stay within
the active implementation phase and must not claim support for unimplemented
features.

## Development

1. Install Python 3.13 and Node.js 22.
2. Run `python -m pip install -e .[dev]`.
3. Run `npm install --prefix frontend`.
4. Run `python scripts/validate_scaffold.py`.
5. Run `pytest`, `ruff check .`, and `mypy`.
6. Run `npm run check --prefix frontend`.

Use conventional commits when practical. Never include GitHub tokens, Home
Assistant secrets, private repository data, authorization headers, signed URLs,
or files copied from a Home Assistant configuration directory.

## Scope

- One repository and HACS entry.
- One `github_insights` custom integration and config entry.
- One shared authentication model and GitHub API client.
- One versioned release artifact containing the backend and every card.
- No separate frontend plugin installation.

See [the implementation plan](docs/implementation-plan.md) before proposing
code.

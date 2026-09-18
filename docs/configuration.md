# Configuration

This is a Phase 1 design, not an available setup flow.

The first release will support one config entry containing one GitHub server,
one authenticated identity, selected organizations, optional enterprise
reporting, and selected/auto-discovered repositories.

Options will cover repository filters, update intervals within safe bounds,
data categories, history granularity, API request limits, archived/forked
repositories, billing scope, currency/cost display, forecasting, security,
traffic, read-only budgets, optional budget management, reference runner/SKU,
and local warning thresholds.

Unavailable categories remain independently disabled with an explanation. The
flow will not request write permissions until the user explicitly enables
budget management.


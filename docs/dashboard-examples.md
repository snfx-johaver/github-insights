# Dashboard examples

Complete tested examples will be added with the frontend implementation. The
planned set covers personal overview, Actions usage/limits, Copilot/AI usage,
repository operations, Home Assistant development, mobile status, security,
and an executive overview using Sections, grid, vertical/horizontal stacks,
native cards, optional Mushroom cards, and GitHub Insights cards.

GitHub Insights will not require Mushroom.

```yaml
type: custom:github-insights-overview
layout: responsive
sections:
  - actions
  - repositories
  - workflows
  - security
```


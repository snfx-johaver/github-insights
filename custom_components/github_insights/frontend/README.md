# Bundled frontend

`github-insights-cards.js` is the deterministic production bundle built from
`frontend/`. HACS installs it inside the `github_insights` integration and the
integration serves it at:

```text
/github_insights/frontend/github-insights-cards.js
```

Register that URL once as a Lovelace JavaScript module resource. The bundle,
backend, and both user-facing cards share one HACS integration installation and
release lifecycle.

# Security policy

## Supported versions

GitHub Insights has not published a functional release. Security fixes will be
provided for the latest supported release after implementation begins.

## Reporting a vulnerability

Do not open a public issue containing a token, private repository information,
Home Assistant diagnostics, or reproduction data with secrets. Use GitHub's
private vulnerability reporting feature for this repository.

Reports should describe impact, affected version, reproduction conditions, and
suggested mitigation without including live credentials.

## Security principles

- Tokens remain only in the Home Assistant config entry.
- Authorization headers, signed URLs, and credentials are redacted from logs
  and diagnostics.
- GitHub Enterprise Server hosts are validated against the configured server;
  arbitrary outbound URLs are rejected.
- Frontend rendering uses text-safe Lit templates and validated links.
- Budget writes are disabled by default and require explicit confirmation.


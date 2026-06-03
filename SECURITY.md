# Security Policy

## Supported Versions

Latest minor release is supported. Older releases receive fixes only for
critical issues.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security reports.**

Email the maintainer with:
- Description of the vulnerability
- Reproduction steps / proof-of-concept
- Affected version(s)
- Impact assessment

Acknowledgement target: 72 hours. Fix target: 14 days for high-severity,
30 days for medium, best effort for low.

## Threat model for generated projects

The scaffold produces a Bearer-token pass-through MCP server. Risks the
generated code addresses by default:

- **Token leakage**: `hash_token` (HMAC-SHA256 with `TELEMETRY_HASH_SALT`) never
  stores raw tokens in telemetry logs.
- **Unauthenticated access**: `RequireAuthMiddleware` rejects requests missing a
  Bearer token before they reach tools.
- **Information disclosure**: `format_error` returns a generic message for
  unknown exceptions; full traceback goes to the log only.
- **CORS**: default `ALLOWED_ORIGINS` is an explicit allow-list (not `*`).

Risks **you** must handle:

- Set `AUTH_PROBE_ENABLED=true` in production so invalid tokens 401 before tools run.
- Rotate `TELEMETRY_HASH_SALT` per deployment; treat it as a secret.
- Restrict `ALLOWED_ORIGINS` to the domains that actually need to connect.
- Run behind HTTPS in production; never expose this server on HTTP publicly.

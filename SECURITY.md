# Security Policy

## Versions I support

I prepare security fixes for the current `main` branch and the latest tagged
release. I do not normally backport fixes to older tags.

## How I receive vulnerability reports

I ask reporters not to place credentials, API keys, database contents, or
unfixed vulnerability details in a public issue.

1. If GitHub shows **Report a vulnerability** on the **Security** tab, I ask the
   reporter to use that private form.
2. If private reporting is unavailable, I ask for an issue titled
   `Security contact requested` without technical details. I will then arrange
   a private communication channel.

I find the affected version, reproducible steps, impact, and a possible fix
helpful. I require all credentials to be removed or replaced with placeholders.

## My security model

- I require `PAPER_ONLY=true`; I refuse to start when it is `false`.
- I expose read-only market-data operations and no order, account, or transfer
  operation.
- If I use a Fusion key, I grant **Read** permission only, never **Trade** or
  **Transfer**.
- I never return the Fusion key through the dashboard or public configuration
  API.
- The Unraid key field is masked for display, but masking is not encryption.
  Unraid can persist the value in its local saved container configuration, so I
  protect `/boot/config` and do not share saved templates or flash backups that
  contain a real key.
- I run the container as UID/GID `99:100`, with a read-only root filesystem, no
  Linux capabilities, and `no-new-privileges`.
- I keep the dashboard inside a trusted LAN or behind a separately secured
  authenticated gateway because the application itself has no login.
- I never commit `.env`, databases, backups, API keys, or registry tokens.
- `.env` is optional for local Docker Compose overrides and is not required by
  the native Unraid deployment.

I document my hardened deployment in [docs/UNRAID.md](docs/UNRAID.md).

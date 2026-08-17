# Maintainer checklist for the visibility switch

I keep this checklist for the final repository and container-package visibility
change. All public usage documentation assumes that both resources are public.
I do not change either visibility setting as part of normal code updates.

## Preparation I complete before the switch

- [x] I keep the application technically paper only.
- [x] I verify that the market client has no order, account, trade, or transfer
      method.
- [x] I run the automated Python, JavaScript, XML, Compose, and release-asset
      checks.
- [x] I build and publish the complete container only after successful tests.
- [x] I verify persistent SQLite data across container recreation.
- [x] I provide an MIT License, disclaimer, security policy, support policy,
      contribution guide, and Code of Conduct.
- [x] I provide a native hardened Unraid template and an English operating guide.
- [x] I publish `latest` from successful `main` builds and immutable
      `sha-<commit>` tags.
- [x] I exclude `.env`, API keys, tokens, databases, backups, and local archives
      from Git.
- [x] I reviewed the repository history available through GitHub and found only
      the empty `FUSION_READ_API_KEY=` placeholder, not a real Fusion key.
- [x] I make `.env` optional for Docker Compose and do not require it on Unraid.
- [x] I document that Unraid's masked API-key field hides the value in the form
      but does not encrypt the locally saved container configuration.
- [x] I keep package, FastAPI, and container metadata on version `0.2.0`.
- [x] I provide Dependabot, issue forms, CODEOWNERS, and a pull-request template.

## The publication actions I perform manually

- [ ] Confirm the latest `main` workflow has completed successfully after the
      final pre-public changes.
- [ ] In **Repository Settings → General → Danger Zone**, change repository
      visibility to **Public**.
- [ ] On the GHCR package settings page, change the container package visibility
      to **Public**.
- [ ] Acknowledge that GitHub does not allow a public container package to be
      changed back to private.
- [ ] In a logged-out environment, verify:

  ```bash
  docker logout ghcr.io
  docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
  ```

- [ ] Open the repository, raw Unraid XML, raw icon, and documentation while
      logged out.
- [ ] Run the public Unraid installation on a clean test container and verify
      the template loads without a `.env` file.

## Optional work after publication

- [ ] Create a version tag in the form `vX.Y.Z` when I want a formal release.
- [ ] Move the `Unreleased` changelog entries into a dated version section.
- [ ] Submit the template to Unraid Community Applications only after the
      anonymous installation test succeeds.
- [ ] Revoke temporary deploy keys or package tokens I no longer need.

# Maintainer checklist for the visibility switch

I keep this checklist for the final repository and container-package visibility
change. All public usage documentation assumes that both resources are public.
I do not change either visibility setting as part of normal code updates.

## Preparation I complete before the switch

- [x] I keep the application technically paper only.
- [x] I verify that the market client has no order, account, trade, or transfer
      method.
- [x] I run the automated Python, JavaScript, XML, and release-asset checks.
- [x] I build the complete container in pull-request CI.
- [x] I verify persistent SQLite data across container recreation.
- [x] I provide an MIT License, disclaimer, security policy, support policy,
      contribution guide, and Code of Conduct.
- [x] I provide a native hardened Unraid template and an English operating guide.
- [x] I publish `latest` from successful `main` builds and immutable
      `sha-<commit>` tags.
- [x] I exclude `.env`, API keys, tokens, databases, and backups from Git.
- [x] I provide Dependabot, issue forms, CODEOWNERS, and a pull-request template.

## The only publication actions I perform manually

- [ ] In **Repository Settings → General → Danger Zone**, I change the
      repository visibility to **Public**.
- [ ] On the GHCR package settings page, I change the container package
      visibility to **Public**.
- [ ] I acknowledge that GitHub does not allow a public container package to be
      changed back to private.
- [ ] In a logged-out environment, I verify:

  ```bash
  docker logout ghcr.io
  docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
  ```

- [ ] I open the repository and its documentation while logged out.
- [ ] I run the public Unraid installation on a clean test container.

## Optional work after publication

- [ ] I create a version tag in the form `vX.Y.Z` when I want a formal release.
- [ ] I move the `Unreleased` changelog entries into a dated version section.
- [ ] I submit the template to Unraid Community Applications only after the
      anonymous installation test succeeds.
- [ ] I revoke temporary deploy keys or package tokens I no longer need.

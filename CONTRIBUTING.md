# Contributing

I welcome focused bug fixes, tests, documentation improvements, and paper-only
strategy research. Before a large change, I recommend opening an issue so I can
review its purpose and safety impact.

## Branch model

The project uses a protected release workflow:

- `main` is the stable public/Community Applications branch.
- `develop` is the integration branch for the next release.
- New work starts from `develop` on a short-lived branch such as `feature/...`,
  `fix/...`, or `docs/...`.
- Feature/fix pull requests target `develop` first.
- A release pull request merges `develop` into `main` only when the intended
  release is complete and all required checks succeed.
- `:latest` is published only from `main` (or release tags), never from
  `develop`.

No change is considered ready for merge while a required GitHub Actions check
is pending or failing.

## Safety boundaries I will not relax

I will not accept a contribution that adds or enables:

- real order creation, modification, cancellation, or confirmation
- account, deposit, withdrawal, or transfer operations
- write access to an exchange API
- a way to start successfully with `PAPER_ONLY=false`
- logging, serving, or embedding API keys and other secrets
- silent increases to the hard risk limits
- claims that the unauthenticated dashboard is safe for direct internet access

Any intentional change to the legal/regulatory boundaries in `LEGAL_SAFETY.md`
requires a fresh review before release.

## How I develop locally

I use Python 3.12 and Node.js and run:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check app/static/app.js
```

I validate the complete container with:

```bash
docker build --pull -t multi-coin-paper-daytrader:test .
```

## What I expect in a pull request

- I expect a concise title and a clear explanation of the problem and change.
- I expect tests and user documentation for behavioural changes.
- I reject generated databases, `.env`, tokens, credentials, and personal market
  data.
- I expect the pull-request checklist to be completed.
- I record user-visible changes under `Unreleased` in `CHANGELOG.md`.
- New feature/fix PRs normally target `develop`; `main` is reserved for release
  PRs and urgent production fixes.

By contributing, the contributor agrees that I may publish the contribution
under this project's [MIT License](LICENSE).

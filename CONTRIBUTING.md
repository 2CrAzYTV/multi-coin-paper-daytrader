# Contributing

I welcome focused bug fixes, tests, documentation improvements, and paper-only
strategy research. Before a large change, I recommend opening an issue so I can
review its purpose and safety impact.

## Safety boundaries I will not relax

I will not accept a contribution that adds or enables:

- real order creation, modification, cancellation, or confirmation
- account, deposit, withdrawal, or transfer operations
- write access to an exchange API
- a way to start successfully with `PAPER_ONLY=false`
- logging, serving, or embedding API keys and other secrets
- silent increases to the hard risk limits
- claims that the unauthenticated dashboard is safe for direct internet access

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

By contributing, the contributor agrees that I may publish the contribution
under this project's [MIT License](LICENSE).

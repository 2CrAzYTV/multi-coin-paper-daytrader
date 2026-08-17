# Changelog

## Unreleased

- I prepared the complete repository for a public English-language release.
- I added a hardened native Unraid template and a matching icon.
- I documented image updates, persistent storage, backup, and digest rollback.
- I added the MIT License, disclaimer, security, support, contribution, and
  conduct policies.
- I added issue forms, a pull-request template, CODEOWNERS, and Dependabot.
- I expanded CI with pull-request tests, Python compilation, XML validation,
  release-asset checks, and a complete container build.
- I added OCI metadata and semantic container tags for versioned releases.
- I translated the dashboard, API messages, and event log to English.

## 0.2.0 – Multi-coin day trading

- I added BTC-EUR, ETH-EUR, SOL-EUR, XRP-EUR, and ADA-EUR as the verified
  default universe.
- I added 15-minute entries with a 1-hour trend filter.
- I applied shared risk, position, and daily limits across every coin.
- I implemented Bitpanda Fusion OHLCV access through read-only GET requests.
- I added the scanner, positions, and multi-coin backtest dashboard.
- I documented the Git and Unraid update flow.
- I excluded gold and silver because their intraday costs do not fit this model.

## 0.1.0 – First paper version

- I created a daily single-asset trend simulation.
- I added three comparison strategies with long/short and leverage variants.
- I added the local SQLite journal and Unraid Docker package.

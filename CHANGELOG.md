# Changelog

## Unreleased

- I added a high-resolution transparent PNG app icon, linked its direct raw URL
  from the Unraid template, and serve the same asset from the container for
  private-installation caching on Unraid.
- I added an English/German dashboard language selector with localized numbers,
  times, scanner results, portfolio details, controls, and known event messages.
- I persist the selected language per browser and expose `APP_LANGUAGE=en|de`
  as the default for new browsers.
- I aligned the Unraid template with my tested installation: one protected
  `.env`, UID/GID 99:100, a read-only filesystem, dropped capabilities, a
  writable `/tmp` tmpfs, PID limit 2048, persistent `/data`, and port 8787.
- I expanded the Unraid template description and guide with the required `.env`
  settings, ownership, permissions, and the warning against duplicate Unraid
  variables that would override `.env`.
- I display sub-euro market prices with four to six decimal places while I keep
  portfolio currency values at two decimal places.
- I explain that scanner prices are closed 15-minute Fusion candle values, so
  they can differ slightly from Bitpanda's continuously changing app quote.
- I document a clean paper-data reset when I switch from demo data to Fusion,
  preventing saved demo snapshots from being mistaken for live market prices.
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

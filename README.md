# Multi-Coin Paper Daytrader – Unraid Edition

[![CI and container image](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/actions/workflows/container-image.yml/badge.svg)](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/actions/workflows/container-image.yml)

Public beta `v0.2.0` of a **paper-only** multi-coin crypto day-trading simulator for Unraid and Docker. It uses €1,000 virtual starting capital by default and cannot place real-money orders.

## Install on Unraid

The public container image is:

```text
ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

The public Unraid template is:

```text
https://raw.githubusercontent.com/2CrAzYTV/multi-coin-paper-daytrader/main/unraid/multi-coin-paper-daytrader.xml
```

No Git checkout, Docker Compose, `.env`, GitHub login, or GHCR token is required on Unraid.

### Quick install for a new Unraid user

1. Open **Docker → Add Container** in Unraid.
2. Use the public XML template from this repository. If the template is not already available in the local template selector, download/import `unraid/multi-coin-paper-daytrader.xml` first.
3. Keep **Repository** set to `ghcr.io/2crazytv/multi-coin-paper-daytrader:latest`.
4. Keep **Persistent Data** at `/mnt/user/appdata/paper-trading-bot/data` unless you deliberately want another location.
5. Keep `PAPER_ONLY=true`.
6. For the first start, keep **Market Data Source** set to `demo`; no API key is needed.
7. Select **Apply**, wait for the container to become healthy, then open `http://UNRAID-IP:8787`.
8. To use current Bitpanda Fusion market data, create your own **Read-only** Fusion API key, change **Market Data Source** to `fusion`, enter the key in the masked **Bitpanda Key** field, and apply the container again. Do not enable Trade or Transfer permission.

The complete installation, update, backup, rollback, and troubleshooting guide is in **[docs/UNRAID.md](docs/UNRAID.md)**.

> The dashboard has no authentication. Keep it inside a trusted LAN and do not expose port 8787 directly to the internet.

## What the simulator compares

The default universe is `BTC-EUR`, `ETH-EUR`, `SOL-EUR`, `XRP-EUR`, and `ADA-EUR`. Each comparison strategy starts with the same €1,000 virtual portfolio:

1. Long only, up to 1× exposure
2. Long/short, up to 1× exposure
3. Long/short, up to 2× exposure

The €1,000 is shared across all configured coins inside each strategy; it is not additional capital per coin.

## Safety contract

This repository deliberately remains **paper only**:

- There is no function that creates, modifies, cancels, or confirms a real order.
- The Bitpanda client exposes read-only `GET` market-data operations.
- The application refuses to start when `PAPER_ONLY=false`.
- Fusion should be used with an API key that has **Read** permission only; never enable **Trade** or **Transfer** for this application.
- The Fusion API key is not returned by the dashboard or public config API.

Bitpanda documents Fusion API-key creation here: [Fusion API key documentation](https://docs.fusion.bitpanda.com/api-key-generation-363384m0).

## Default risk limits

| Rule | Default | Effect with €1,000 |
| --- | ---: | ---: |
| Modelled risk per trade | 0.5% | approximately €5 maximum |
| Aggregate open risk | 1% | approximately €10 maximum |
| Daily loss limit | 2% | approximately €20 maximum |
| Simultaneous positions | 2 | shared across all coins |
| New trades per day | 3 | shared across all coins |
| Persistent emergency stop | 10% drawdown | closes and locks until reset |
| Maximum leverage | 2× | comparison strategy 3 only |

Position sizing uses stop distance and includes assumed fees and slippage. Real markets can gap beyond stops, so these are simulation limits rather than guarantees.

## Strategy defaults

- 15-minute signal interval
- 1-hour trend filter
- fresh EMA-9/EMA-21 crossover in the direction of the hourly trend
- RSI and relative candle-volume filters
- stop distance equal to the larger of `1.5 × ATR(14)` and `0.6%`
- `2R` profit target
- stop moved to break-even after `1R`
- 45-minute per-pair cooldown after an exit
- all open positions closed at 23:45 in `Europe/Berlin`

The application requests active pairs and skips unavailable markets. Fusion documents the read-only [pair list](https://docs.fusion.bitpanda.com/get-trading-pairs-4295528e0) and [OHLCV candle](https://docs.fusion.bitpanda.com/get-candles-4311313e0) endpoints used by the project.

## Fusion key on Unraid

The Unraid field uses `Mask="true"`, which hides the key in the form but **does not encrypt it**. Unraid can persist container-variable values in its local Docker-template configuration. Protect `/boot/config` and its backups, and never share a saved local template that contains a real key.

## Source / Docker Compose installation

Docker Compose works without a `.env` file because safe defaults are built in:

```bash
git clone https://github.com/2CrAzYTV/multi-coin-paper-daytrader.git paper-trading-bot
cd paper-trading-bot
mkdir -p data
chown -R nobody:users data
docker compose up -d --build
```

Open `http://HOST-IP:8787` and inspect it with:

```bash
docker compose ps
docker compose logs --tail=100 paper-trading-bot
```

The SQLite database stays at `./data/paper_trading.sqlite3` outside version control.

A `.env` file is optional for local Compose overrides. `.env.example` is only a reference/template. Never commit a populated `.env`.

To use Fusion locally without `.env`:

```bash
DATA_SOURCE=fusion \
FUSION_READ_API_KEY='MY_LOCAL_READ_ONLY_KEY' \
docker compose up -d --build
```

Never commit, publish, or paste a real API key into an issue or support request.

## Updates

Every successful push to `main` is tested by GitHub Actions and publishes a new `:latest` image plus an immutable `sha-*` tag. On Unraid use **Docker → Check for Updates → Update/Force Update**. The `/data` bind mount survives container recreation.

An image update does not automatically replace the locally saved Unraid template. If a release adds or removes template fields, recreate the container from the current public XML while keeping the same persistent `/data` mapping. Backup and digest rollback are documented in [docs/UNRAID.md](docs/UNRAID.md#updates-backup-and-rollback).

## Dashboard controls

- **Language:** switch the complete dashboard between English and German.
- **Run scan now:** retrieve the latest closed candle without processing the same candle twice.
- **Run multi-coin backtest:** simulate all configured pairs with one shared risk budget without changing active paper portfolios.
- **Reset paper data:** delete only the local simulation state.

The default poll interval is 60 seconds, but the strategy can trade at most once per newly closed 15-minute candle. A signal does not guarantee a trade.

## Configuration guardrails

The application reads standard environment variables. Unraid supplies them through the native template; Compose supplies safe defaults and accepts optional shell/`.env` overrides.

Code-enforced limits include:

- `APP_LANGUAGE` must be `en` or `de`
- `RISK_PER_TRADE` at most `0.01`
- `MAX_AGGREGATE_RISK` at most `0.02`
- `MAX_DAILY_LOSS` at most `0.02`
- `MAX_OPEN_POSITIONS` at most `3`
- `MAX_TRADES_PER_DAY` at most `6`
- `PAPER_ONLY` must remain `true`

## Tests

The core local/CI checks are:

```bash
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check app/static/app.js
python -c "import xml.etree.ElementTree as ET; ET.parse('unraid/multi-coin-paper-daytrader.xml')"
docker compose config
```

Pull requests also build the complete Docker image before merge. The protected `main` branch requires the `Test application` status check to pass.

## Limitations and disclaimer

- No return or side-income promise is made.
- Short history and overfitting can make backtests misleading.
- Fees and slippage are modelled; every real execution detail is not reproduced.
- Correlated crypto assets are not treated as true diversification.
- Taxes are not calculated.
- Extended paper testing is required before drawing conclusions.
- Real-money trading is intentionally outside this repository.

## Project policies

This project is published under the [MIT License](LICENSE). Also see:

- [Disclaimer](DISCLAIMER.md)
- [Security policy](SECURITY.md)
- [Support policy](SUPPORT.md)
- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)

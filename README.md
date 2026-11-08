# Multi-Coin Paper Trader – Unraid Edition

[![CI and container image](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/actions/workflows/container-image.yml/badge.svg)](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/actions/workflows/container-image.yml)

Public beta `v0.4.0` of a **paper-only** crypto trend-following simulator for Unraid and Docker. It simulates one realistic Bitpanda Fusion **spot** account (long only, no leverage, real fees, order-book prices), uses €1,000 virtual starting capital by default and cannot place real-money orders.

> The repository and image keep the historic name `multi-coin-paper-daytrader`. Since v0.3.0 the simulator no longer day-trades - see [Why not intraday](#why-not-intraday).

## Install on Unraid

The public container image is:

```text
ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

The canonical public Unraid / Community Applications template is:

```text
https://raw.githubusercontent.com/2CrAzYTV/multi-coin-paper-daytrader/main/templates/multi-coin-paper-daytrader.xml
```

No Git checkout, Docker Compose, `.env`, GitHub login, or GHCR token is required on Unraid.

### Quick install for a new Unraid user

1. Open **Docker → Add Container** in Unraid.
2. Use the public XML template from this repository. If the template is not already available in the local template selector, download/import `templates/multi-coin-paper-daytrader.xml` first.
3. Keep **Repository** set to `ghcr.io/2crazytv/multi-coin-paper-daytrader:latest`.
4. Keep **Persistent Data** at `/mnt/user/appdata/paper-trading-bot/data` unless you deliberately want another location.
5. Keep `PAPER_ONLY=true`.
6. For the first start, keep **Market Data Source** set to `demo`; no API key is needed.
7. Select **Apply**, wait for the container to become healthy, then open `http://UNRAID-IP:8787`.
8. To use current Bitpanda Fusion market data, create your own **Read-only** Fusion API key, change **Market Data Source** to `fusion`, enter the key in the masked **Bitpanda Key** field, and apply the container again. Do not enable Trade or Transfer permission.

The complete installation, update, backup, rollback, and troubleshooting guide is in **[docs/UNRAID.md](docs/UNRAID.md)**.

> The dashboard has no authentication. Keep it inside a trusted LAN and do not expose port 8787 directly to the internet.

## Strategy: Donchian trend following (one strategy, spot only)

The default universe is `BTC-EUR`, `ETH-EUR`, `SOL-EUR` and `XRP-EUR` - the only Fusion EUR pairs with more than €10 million daily volume and spreads of about 1-2 basis points (measured November 2026; `ADA-EUR` was dropped at ~18 bp spread).

Rules, evaluated once per closed **daily** candle (classic "Turtle System 2"):

- **Buy** when the daily close is above the highest high of the previous `ENTRY_WINDOW` (55) days
- **Sell** when the daily close is below the lowest low of the previous `EXIT_WINDOW` (20) days
- both channels exclude the current candle (no look-ahead)
- each position gets an equal share of equity (`1 / number of pairs`), raised to the exchange minimum order if the share is smaller and the cash allows it
- long only, no short selling, no leverage, never more than the available cash
- simultaneous buy signals are ranked by breakout strength (distance above the channel in ATR)

## Realism model

| Item | Model |
| --- | --- |
| Fee | `FEE_RATE=0.0025` per order - Bitpanda Fusion entry tier (< €100k 30-day volume) |
| Live fills | volume-weighted price walked through the **real Fusion order book** (read-only `GET /v1/orderbook/{pair}`), incl. spread and depth |
| Backtest fills | daily close ± `SLIPPAGE_RATE` (0.05%) |
| Order limits | Fusion `minOrderAmount`, `maxOrderAmount` and `sizeIncrement` per pair |
| Account | one spot account: cash + coins, no margin |
| Backtest history | up to 1,440 daily candles (~4 years) from Fusion |

Not modelled: exchange outages and the exact minute of execution after the daily close.

## German tax model

Crypto sales within one year of the purchase are private sales (§ 23 EStG); after one year they are tax-free. The simulator models this in the live account and in the backtest:

- every closed trade records its holding period and whether it is taxable
- per calendar year the taxable results are netted; below the **Freigrenze** (`TAX_FREE_LIMIT`, €1,000) the year stays tax-free, at or above it the whole amount is taxed at `TAX_RATE` (default 30%, approximate personal marginal rate incl. solidarity surcharge)
- net losses are carried forward; the tax of a finished year is deducted from the paper account at the year change
- the backtest reports results before and after tax; buy-and-hold over more than a year is tax-free

Simplifications: church tax, your other private sales (which share the same Freigrenze) and the real payment date are not modelled. This is a simulation aid, not tax advice.

What it means (4 years of Fusion data, 30% tax): with €100 the yearly gains stay below the Freigrenze and the strategy returns +46.8%/year after tax vs. +37.7% for buy-and-hold; from about €1,000 upwards the tax brings it down to +31.6%/year, **below** tax-free buy-and-hold (+37.7%/year) - but with a much smaller drawdown (39% vs. 70%).

## Why not intraday

Before v0.3.0 the simulator day-traded 15-minute candles. Tested on one year of real Fusion 15-minute data (Nov 2025 - Nov 2026) with the real fee of 0.25% per order, every intraday variant lost money in both half-years - the EMA crossover, and Opening Range Breakouts at 09:00 and 15:30. Before costs the ORB variants had a small but consistent edge (≈ +3-4% per half-year); a round trip costs ≈ 0.6%, several times the average gross gain per trade.

The same daily Donchian rule on four years of Fusion daily data (Nov 2022 - Nov 2026, 4 pairs, real fees) returned about **+39% per year with a 30% maximum drawdown**, versus +38% per year and a 70% drawdown for equal-weight buy-and-hold, with only ~34 trades. That is one sample from a market that rose strongly; it is evidence for the approach, not a promise.

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

An image update does not automatically replace the locally saved Unraid template. If a release adds or removes template fields, recreate the container from the current canonical public XML under `templates/` while keeping the same persistent `/data` mapping. Backup and digest rollback are documented in [docs/UNRAID.md](docs/UNRAID.md#updates-backup-and-rollback).

## Dashboard controls

- **Language:** switch the complete dashboard between English and German.
- **Run scan now:** retrieve the latest closed candle without processing the same candle twice.
- **Run 4-year backtest:** simulate the strategy and equal-weight buy-and-hold with the same costs, without changing the paper account.
- **Reset paper data:** delete only the local simulation state.

The default poll interval is 300 seconds. A new decision happens only once per closed daily candle (00:00 UTC); between candles the open positions are marked to the live order-book mid price.

## Configuration guardrails

Code-enforced limits include:

- `APP_LANGUAGE` must be `en` or `de`
- `PAPER_ONLY` must remain `true`
- `CANDLE_INTERVAL` must be `1d` or `4h`
- `2 <= EXIT_WINDOW < ENTRY_WINDOW <= 250`
- `FEE_RATE` and `SLIPPAGE_RATE` between 0 and 1%
- `MAX_OPEN_POSITIONS` between 1 and the number of `PAIRS`

## Upgrading from v0.2

v0.3.0 stores its data in new `tf_*` tables. The old intraday `dt_*` tables stay untouched in the same SQLite file; nothing is migrated or deleted. Obsolete variables (`RISK_PER_TRADE`, `MAX_DAILY_LOSS`, EMA/ADX/RSI windows, session close, cooldown, …) are ignored and can be removed from the template.

## Tests

The core local/CI checks are:

```bash
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check app/static/app.js
python -c "import xml.etree.ElementTree as ET; ET.parse('templates/multi-coin-paper-daytrader.xml')"
docker compose config
```

Pull requests also build the complete Docker image before merge. The protected `main` branch requires the `Test application` status check to pass.

## Limitations and disclaimer

- No return or side-income promise is made.
- Four years of daily data contain only a few dozen trades; overfitting and luck can make backtests misleading.
- Trend following has long flat or losing periods (e.g. 2025-2026 in the backtest).
- Fees, spread and order-book depth are modelled; every real execution detail is not reproduced.
- Correlated crypto assets are not treated as true diversification.
- Taxes are not calculated.
- Extended paper testing is required before drawing conclusions.
- Real-money trading is intentionally outside this repository.

## Project policies

This project is published under the [MIT License](LICENSE). Also see:

- [Disclaimer](DISCLAIMER.md)
- [Legal safety boundaries](LEGAL_SAFETY.md)
- [Security policy](SECURITY.md)
- [Support policy](SUPPORT.md)
- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)

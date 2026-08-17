# Multi-Coin Paper Daytrader – Unraid Edition

[![CI and container image](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/actions/workflows/container-image.yml/badge.svg)](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/actions/workflows/container-image.yml)

I built this project as a fully simulated day-trading environment with
**€1,000 of virtual starting capital**. I monitor five liquid EUR crypto
markets by default and compare three approaches under the same market
conditions:

1. **Long only, up to 1× exposure**
2. **Long/short, up to 1× exposure**
3. **Long/short, up to 2× exposure**

My default universe is `BTC-EUR`, `ETH-EUR`, `SOL-EUR`, `XRP-EUR`, and
`ADA-EUR`. I treat the €1,000 in each comparison strategy as one shared
portfolio, not as additional capital for every coin.

## My safety contract

I deliberately keep this project **paper only**:

- I do not include any function that creates, modifies, cancels, or confirms a
  real order.
- My Bitpanda client exposes read-only `GET` market-data operations.
- I refuse to start when `PAPER_ONLY=false`.
- If I enable live Fusion market data, I use an API key with **Read** permission
  only. I never enable **Trade** or **Transfer**.
- I never return the Fusion API key through the dashboard or public config API.

I follow Bitpanda's official
[Fusion API key documentation](https://docs.fusion.bitpanda.com/api-key-generation-363384m0)
when I create a read-only key.

## Shared portfolio risk limits

| Rule | Default | Effect with €1,000 |
| --- | ---: | ---: |
| Modelled risk per trade | 0.5% | approximately €5 maximum |
| Aggregate open risk | 1% | approximately €10 maximum |
| Daily loss limit | 2% | approximately €20 maximum |
| Simultaneous positions | 2 | shared across all coins |
| New trades per day | 3 | shared across all coins |
| Persistent emergency stop | 10% drawdown | I close and lock until reset |
| Maximum leverage | 2× | comparison strategy 3 only |

I size positions from the stop distance and include assumed fees and slippage.
Real markets can gap beyond a stop, so I treat these limits as a conservative
simulation model rather than a loss guarantee.

## Strategy

I use the following rules:

- 15-minute signal interval
- 1-hour trend filter
- fresh EMA-9/EMA-21 crossover in the direction of the hourly trend
- RSI and relative candle-volume filters
- stop distance equal to the larger of `1.5 × ATR(14)` and `0.6%`
- `2R` profit target
- stop moved to break-even after `1R`
- 45-minute per-pair cooldown after an exit
- all open positions closed at 23:45 in `Europe/Berlin`

I request the pairs that Bitpanda reports as active and skip unavailable
markets. Fusion documents the read-only
[pair list](https://docs.fusion.bitpanda.com/get-trading-pairs-4295528e0) and
[OHLCV candle](https://docs.fusion.bitpanda.com/get-candles-4311313e0)
endpoints I use.

## Why I do not include precious metals

I consider gold and silver useful for long-term diversification, but I do not
apply this 15-minute strategy to them. Bitpanda currently describes combined
buying and selling premiums of approximately **1.5% for gold** and **4.5% for
silver**. I consider those costs too high relative to my 2% daily loss limit.
Source: [Bitpanda Metals](https://support.bitpanda.com/hc/en-us/articles/360004208619-What-is-Bitpanda-Metals).

## My recommended Unraid installation

I publish the ready-to-run image at:

```text
ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

I do not need Git, Docker Compose, or a `.env` file on Unraid. The native Unraid
template exposes the complete application configuration as container variables,
including the masked **Bitpanda Key** field.

My complete guide covers the native **Add Container** form, the included Unraid
XML template, hardened runtime options, persistent storage, health checks,
updates, backups, rollback, and troubleshooting:

➡️ **[How I install and operate the bot on Unraid](docs/UNRAID.md)**

I open the dashboard at `http://UNRAID-IP:8787`. The dashboard has no login, so
I expose it only inside a trusted LAN and never directly to the internet.

### Important note about the Fusion key on Unraid

`Mask="true"` hides the key in the Unraid form, but masking is **not encryption**.
Unraid may persist container-variable values in its local Docker template
configuration. I therefore never share my local template XML or `/boot/config`
backup while it contains a real API key. I use a Fusion key with **Read**
permission only.

## Source installation

When I develop or build locally, Docker Compose works without creating a `.env`
file because the compose file contains safe defaults:

```bash
git clone https://github.com/2CrAzYTV/multi-coin-paper-daytrader.git paper-trading-bot
cd paper-trading-bot
mkdir -p data
chown -R nobody:users data
docker compose up -d --build
```

I then open `http://HOST-IP:8787` and inspect the service with:

```bash
docker compose ps
docker compose logs --tail=100 paper-trading-bot
```

I keep the SQLite database at `./data/paper_trading.sqlite3` outside version
control.

A `.env` file remains **optional** for source/Compose users who want persistent
local overrides. Docker Compose automatically reads it for variable
interpolation, but this project no longer requires `env_file:` and does not
need `.env` to start in demo mode. `.env.example` is only a reference/template.

For example:

```bash
cp .env.example .env
chmod 600 .env
```

I never commit a populated `.env`.

## Updates

After every successful push to `main`, my GitHub Actions workflow tests the
project and publishes a new `:latest` image plus an immutable `sha-*` tag. This
makes Unraid's image-update detection work.

I update the running container from **Docker → Check for Updates →
Update/Force Update**. Unraid pulls the new image and recreates the container
from its saved template. The `/data` bind mount remains intact.

I do not expect `docker restart` or `--restart=unless-stopped` to pull an image;
they only restart the already installed image. I document backup and digest
rollback in [docs/UNRAID.md](docs/UNRAID.md#updates-backup-and-rollback).

## Demo and read-only Fusion data

I start with `DATA_SOURCE=demo`, which produces deterministic offline data. On
Unraid I switch **Market Data Source** to `fusion` and fill the masked
**Bitpanda Key** field.

For Docker Compose/source usage I can either export variables in the shell or
use the optional `.env` file. Example with shell variables:

```bash
DATA_SOURCE=fusion \
FUSION_READ_API_KEY='MY_LOCAL_READ_ONLY_KEY' \
docker compose up -d --build
```

I never commit, publish, or paste the real key into a chat or issue.

## Dashboard controls

- **Language:** I switch the complete dashboard between English and German.
  The browser stores my selection, while `APP_LANGUAGE=en` or
  `APP_LANGUAGE=de` defines the default for a new browser.
- **Run scan now:** I retrieve the latest closed candle and never process the
  same candle twice.
- **Run multi-coin backtest:** I simulate all configured pairs with one shared
  risk budget without changing the active paper portfolios.
- **Reset paper data:** I delete only the local simulation state.

I poll every 60 seconds by default, but I can trade at most once per newly
closed 15-minute candle. A signal does not guarantee a trade. Quiet days with
no trades are normal, and the global default allows no more than three new
entries per day.

## Configuration

The application reads standard environment variables. Unraid provides them from
the native template, while Docker Compose provides safe defaults and accepts
optional shell/`.env` overrides. `.env.example` documents the available values.

I also enforce these limits in code:

- `APP_LANGUAGE` must be `en` or `de`
- `RISK_PER_TRADE` at most `0.01`
- `MAX_AGGREGATE_RISK` at most `0.02`
- `MAX_DAILY_LOSS` at most `0.02`
- `MAX_OPEN_POSITIONS` at most `3`
- `MAX_TRADES_PER_DAY` at most `6`
- `PAPER_ONLY` must remain `true`

## Tests

I run the same core checks locally and in CI:

```bash
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check app/static/app.js
python -c "import xml.etree.ElementTree as ET; ET.parse('unraid/multi-coin-paper-daytrader.xml')"
docker compose config
```

For pull requests, CI also builds the complete Docker image before I merge.

## Limitations

- I do not promise returns or reliable side income.
- I know that short history and overfitting can make a backtest misleading.
- I model fees and slippage; I do not reproduce every real execution detail.
- I do not treat several correlated crypto assets as true diversification.
- I do not calculate taxes.
- I require extended paper testing before drawing conclusions. Real-money
  trading is intentionally outside this repository.

## Project policies

I publish this project under the [MIT License](LICENSE). Before using or
contributing, I recommend reading:

- [Disclaimer](DISCLAIMER.md)
- [Security policy](SECURITY.md)
- [Support policy](SUPPORT.md)
- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Public visibility switch checklist](docs/RELEASE_CHECKLIST.md)

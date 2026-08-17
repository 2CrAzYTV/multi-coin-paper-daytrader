# Install and operate Multi-Coin Paper Daytrader on Unraid

This guide is written for a new user installing the public beta on an Unraid server. No Git checkout, Docker Compose, `.env`, GitHub login, or GHCR token is required.

## Public release resources

Container image:

```text
ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

Unraid XML template:

```text
https://raw.githubusercontent.com/2CrAzYTV/multi-coin-paper-daytrader/main/unraid/multi-coin-paper-daytrader.xml
```

Repository:

```text
https://github.com/2CrAzYTV/multi-coin-paper-daytrader
```

The dashboard has no login. Keep port `8787` inside a trusted LAN and never expose it directly through a router port-forward.

## 1. Clean installation

### Prepare persistent app data

Run once in the Unraid terminal:

```bash
mkdir -p /mnt/user/appdata/paper-trading-bot/data
chown -R nobody:users /mnt/user/appdata/paper-trading-bot/data
chmod 775 /mnt/user/appdata/paper-trading-bot/data
```

The container runs without root privileges as UID/GID `99:100`. These permissions allow SQLite to create and update the database.

### Confirm the public image is anonymously accessible

This is optional but useful for troubleshooting:

```bash
docker logout ghcr.io 2>/dev/null || true
docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

No token or registry login should be required.

### Load the Unraid template

Use the public XML template from this repository. The included `unraid/multi-coin-paper-daytrader.xml` contains the image reference, WebUI, icon, data mapping, hardened runtime options and all application variables.

For a first installation, keep these important values:

```text
Repository: ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
WebUI Port: 8787
Persistent Data: /mnt/user/appdata/paper-trading-bot/data
PAPER_ONLY: true
Market Data Source: demo
Bitpanda Key: empty
Application Timezone: Europe/Berlin
UI Language: de
```

Select **Apply**. The first start in `demo` mode needs no external API key.

## 2. Verify the first start

Run:

```bash
docker inspect paper-trading-bot \
  --format 'Status={{.State.Status}} Health={{.State.Health.Status}} Image={{.Config.Image}}'
curl -fsS http://127.0.0.1:8787/health
docker logs --tail=50 paper-trading-bot
```

Expected health response in demo mode:

```json
{"status":"ok","paper_only":true,"data_source":"demo"}
```

Open the dashboard at:

```text
http://UNRAID-IP:8787
```

A successful clean install therefore means: container `running`, health `healthy`, `/health` returns HTTP 200, and the dashboard opens without any previous appdata or local template state.

## 3. Enable read-only Bitpanda Fusion market data

Only after the demo-mode clean install works:

1. Create a Bitpanda Fusion API key with **Read** permission only.
2. Do **not** enable **Trade** or **Transfer**.
3. Edit the Unraid container.
4. Change **Market Data Source** from `demo` to `fusion`.
5. Enter the key in the masked **Bitpanda Key** field.
6. Select **Apply**.
7. Verify:

```bash
curl -fsS http://127.0.0.1:8787/health
```

Expected:

```json
{"status":"ok","paper_only":true,"data_source":"fusion"}
```

`Mask="true"` hides the key in the Unraid form but **does not encrypt it**. Unraid can persist container-variable values in its local Docker-template configuration. Protect `/boot/config` and its backups, and never share a saved local template containing a real key.

## 4. Default application configuration

The template exposes these defaults:

```dotenv
PAPER_ONLY=true
STARTING_CAPITAL=1000
RISK_PER_TRADE=0.005
MAX_AGGREGATE_RISK=0.01
MAX_DAILY_LOSS=0.02
HARD_DRAWDOWN=0.10
MAX_OPEN_POSITIONS=2
MAX_TRADES_PER_DAY=3
FEE_RATE=0.001
SLIPPAGE_RATE=0.0005
PAIRS=BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR,ADA-EUR
CANDLE_INTERVAL=15m
TREND_INTERVAL=1h
FAST_WINDOW=9
SLOW_WINDOW=21
TREND_FAST_WINDOW=20
TREND_SLOW_WINDOW=50
ATR_WINDOW=14
RSI_WINDOW=14
STOP_ATR_MULTIPLE=1.5
MINIMUM_STOP_PCT=0.006
TAKE_PROFIT_R=2.0
TRAILING_TRIGGER_R=1.0
HISTORY_BARS=500
BACKTEST_BARS=1000
DATA_SOURCE=demo
FUSION_READ_API_KEY=
FUSION_BASE_URL=https://api.fusion.bitpanda.com
APP_TIMEZONE=Europe/Berlin
POLL_SECONDS=60
SESSION_CLOSE_HOUR=23
SESSION_CLOSE_MINUTE=45
COOLDOWN_MINUTES=45
APP_LANGUAGE=de
DATA_DIR=/data
TZ=Europe/Berlin
```

The WebUI maps to port `8787`; persistent data maps `/mnt/user/appdata/paper-trading-bot/data` to `/data`. Hardened Extra Parameters are:

```text
--user=99:100 --read-only --init --tmpfs=/tmp:size=64m,mode=1777 --security-opt=no-new-privileges:true --cap-drop=ALL --pids-limit=2048 --restart=unless-stopped --stop-timeout=20
```

`PAPER_ONLY=true` must remain enabled. The application rejects a configuration that disables paper-only mode and contains no real-money order implementation.

## 5. Language

The template defaults `APP_LANGUAGE=de`. Set it to `en` before applying if preferred. The dashboard language selector can switch English/German immediately; the browser stores that choice locally.

## Updates, backup, and rollback

### Updates

Every successful push to `main` runs tests and publishes a new `:latest` image plus an immutable `sha-<commit>` tag.

On Unraid:

1. **Docker → Check for Updates**
2. **Update** or **Force Update** on `paper-trading-bot`
3. verify health, logs, and dashboard

The `/data` bind mount survives recreation.

Important: an image update does not necessarily update an already-saved local Unraid template. If a release adds or removes template fields, recreate the container from the current public XML while keeping the same persistent `/data` mapping.

`docker restart` and `--restart=unless-stopped` do not pull new images.

### Back up SQLite

For a consistent backup:

```bash
docker stop paper-trading-bot
cp -a \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3 \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3.backup
docker start paper-trading-bot
```

### Record and restore an image digest

Before an update:

```bash
docker image inspect \
  ghcr.io/2crazytv/multi-coin-paper-daytrader:latest \
  --format '{{index .RepoDigests 0}}'
```

For rollback, temporarily replace `:latest` in the Unraid **Repository** field with the complete `@sha256:…` reference and select **Apply**.

## Troubleshooting

### `unauthorized` while pulling

The public package does not require authentication. Remove stale credentials and retry:

```bash
docker logout ghcr.io
docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

### WebUI does not open

```bash
docker ps --filter 'name=paper-trading-bot'
docker port paper-trading-bot
curl -I --max-time 5 http://127.0.0.1:8787/
curl -I --max-time 5 http://UNRAID-IP:8787/
```

Expect `8787/tcp` to map to `0.0.0.0:8787` or the intended LAN address.

### Fusion prices differ from the Bitpanda app

Confirm the dashboard reports **Bitpanda Fusion**. The scanner displays the close of the latest completed 15-minute Fusion candle; the Bitpanda app can display a continuously changing quote, so a time-dependent difference is expected.

If switching an existing simulation from demo to Fusion, the database can still contain old demo snapshots. For a clean Fusion simulation use **Reset my paper accounts → Delete paper data**, then **Run scan now**.

## Community Applications status

The repository already contains a public Unraid XML template and public GHCR image, which are the core technical assets required for distribution. **Being installable from a public template is not the same as being listed in Unraid Community Applications.** A Community Applications listing requires the separate CA publication/submission process and should only be done after the clean-install test and public beta release are confirmed.

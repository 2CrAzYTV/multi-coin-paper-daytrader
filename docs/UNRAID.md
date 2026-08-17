# How I install and operate the bot on Unraid

I use the published container image directly, so I do not need a Git checkout
or Docker Compose on my Unraid server. The dashboard has no login. I bind port
`8787` only inside a trusted LAN and never expose it through a router port
forward.

## 1. I prepare persistent app data

I run this once in the Unraid terminal:

```bash
mkdir -p /mnt/user/appdata/paper-trading-bot/data
chown -R nobody:users /mnt/user/appdata/paper-trading-bot/data
chmod 775 /mnt/user/appdata/paper-trading-bot/data
```

I deliberately run the container without root privileges as UID/GID `99:100`.
These permissions allow SQLite to create and update the database without
weakening that runtime restriction.

A separate `.env` file is not required when I use the included Unraid template.
The template exposes the important application settings directly as Unraid
container variables and also includes the complete advanced strategy defaults.

## 2. I use the public image

I use this repository value in Unraid:

```text
ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

The public image requires no GHCR token or `docker login`. If I want to test
the pull first, I run:

```bash
docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

## 3. I create the container from the template

The included
[`unraid/multi-coin-paper-daytrader.xml`](../unraid/multi-coin-paper-daytrader.xml)
contains the image, WebUI, icon, data mapping, hardened runtime and bot defaults.
The main fields shown directly in the Unraid template are:

| Field | Default |
| --- | --- |
| Name | `paper-trading-bot` |
| Repository | `ghcr.io/2crazytv/multi-coin-paper-daytrader:latest` |
| Network Type | `bridge` |
| WebUI | `http://[IP]:[PORT:8787]/` |
| WebUI Port | `8787` |
| Persistent Data | `/mnt/user/appdata/paper-trading-bot/data` → `/data` |
| UI Language | `de` |
| Market Data Source | `demo` |
| Starting Paper Capital | `1000` EUR |
| Risk per Trade | `0.005` = 0.5% |
| Maximum Aggregate Risk | `0.01` = 1% |
| Maximum Daily Loss | `0.02` = 2% |
| Maximum Open Positions | `2` |
| Maximum Trades per Day | `3` |
| Trading Pairs | `BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR,ADA-EUR` |
| Candle Interval | `15m` |
| Trend Interval | `1h` |

The Fusion API key field is masked in the Unraid form. I only fill it when I
select `DATA_SOURCE=fusion`, and I create the Bitpanda Fusion key with **Read**
permission only while leaving **Trade** and **Transfer** disabled.

Under **Show more settings** / advanced view, the template also exposes the
remaining strategy and runtime defaults such as hard drawdown, fee and slippage
rates, EMA/ATR/RSI windows, stop and take-profit parameters, history/backtest
bars, poll interval, session close time, cooldown, application timezone,
`DATA_DIR`, `FUSION_BASE_URL`, and the `PAPER_ONLY=true` safety lock.

The template uses these **Extra Parameters**:

```text
--user=99:100 --read-only --init --tmpfs=/tmp:size=64m,mode=1777 --security-opt=no-new-privileges:true --cap-drop=ALL --pids-limit=2048 --restart=unless-stopped --stop-timeout=20
```

I keep `PAPER_ONLY=true`. This release rejects any configuration that disables
paper-only mode and cannot place real-money orders.

## 4. I verify the first start

After I select **Apply**, I expect Unraid to report `healthy`. I also run:

```bash
docker inspect paper-trading-bot \
  --format 'Status={{.State.Status}} Health={{.State.Health.Status}} Image={{.Config.Image}}'
curl -fsS http://127.0.0.1:8787/health
docker logs --tail=50 paper-trading-bot
```

In demo mode I expect:

```json
{"status":"ok","paper_only":true,"data_source":"demo"}
```

I open the dashboard at `http://UNRAID-IP:8787`.

## 5. I select English or German

The Unraid template defaults `APP_LANGUAGE=de`. I can change that field to
`en` before applying the container. I can also use the language selector in the
top bar to switch the complete dashboard between English and German immediately.
The browser stores my selection on that device.

A stored browser selection takes precedence over the container default. Changing
the selector does not restart the container and does not alter paper trades,
strategy rules, or market data.

## 6. I enable read-only current market data

I change **Market Data Source** from `demo` to `fusion` and fill **Bitpanda
Fusion Read API Key**. I create that key with **Read** permission only and leave
**Trade** and **Transfer** disabled. I then select **Apply** so Unraid recreates
the container with the changed environment variables.

## Updates, backup, and rollback

### How my updates work

Every successful push to `main` runs tests and publishes a new `:latest`
image. The workflow also publishes an immutable `sha-<commit>` tag. Because my
Unraid template tracks `:latest`, Unraid can detect a changed registry digest.

I install an update with:

1. **Docker → Check for Updates**
2. **Update** or **Force Update** on `paper-trading-bot`
3. verify health, logs, and the dashboard

Unraid pulls the changed image and recreates the container from its saved
template. My bind mount at
`/mnt/user/appdata/paper-trading-bot/data` survives this process.

Important: Unraid keeps the locally saved template of an existing container.
If the repository template itself gains new fields, an ordinary image update
may not automatically add those new XML entries to the already-installed
container form. In that case I open the container for editing and use the
current repository template as reference, or recreate the container from the
updated template while keeping the same persistent `/data` mapping.

I know that `docker restart` and `--restart=unless-stopped` do not pull a new
image. They only restart the locally installed image. The `:latest` workflow
is also compatible with an Unraid automatic-update feature if I deliberately
enable one, but I prefer controlled updates for a trading simulation.

### How I back up SQLite

For a consistent backup, I briefly stop the container:

```bash
docker stop paper-trading-bot
cp -a \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3 \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3.backup
docker start paper-trading-bot
```

### How I record and restore an image digest

Before an update, I record the exact installed digest:

```bash
docker image inspect \
  ghcr.io/2crazytv/multi-coin-paper-daytrader:latest \
  --format '{{index .RepoDigests 0}}'
```

To roll back, I temporarily replace `:latest` in the Unraid **Repository**
field with the full `@sha256:…` reference and select **Apply**. I use a digest
because it identifies one immutable image, while `latest` moves.

## Troubleshooting

### My market prices do not appear to match Bitpanda

I first check that the dashboard reports **Bitpanda Fusion** as its data source.
The scanner displays the close of the latest completed 15-minute Fusion candle,
while the Bitpanda app displays a continuously changing quote. I therefore
expect a small time- and venue-dependent difference.

I display market prices below €1 with four decimal places and prices below
€0.01 with six decimal places. I keep portfolio balances at two decimal places.
This prevents values such as €0.8649 from appearing only as €0.87 without
changing the full-precision values used by the simulation.

If I have just changed `DATA_SOURCE=demo` to `DATA_SOURCE=fusion`, my database
may still contain the last saved demo snapshots. For a clean Fusion simulation,
I use **Reset my paper accounts → Delete paper data**, confirm the deletion, and
then select **Run scan now**. This deletes local simulated balances, positions,
trades, and cached market snapshots, but it does not delete the container
configuration or Fusion API key.

Before deleting paper data that I want to preserve, I create a database backup
as described above.

### I receive `unauthorized` while pulling

The public image does not require a registry login. I remove stale credentials
and retry:

```bash
docker logout ghcr.io
docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

### My container runs but the WebUI does not open

I check the binding and both local routes:

```bash
docker ps --filter 'name=paper-trading-bot'
docker port paper-trading-bot
curl -I --max-time 5 http://127.0.0.1:8787/
curl -I --max-time 5 http://UNRAID-IP:8787/
```

I expect `8787/tcp` to map to `0.0.0.0:8787` or my intended LAN address. I
also check the browser cache, local firewall, and VLAN rules.

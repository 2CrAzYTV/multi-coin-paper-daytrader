# How I install and operate the bot on Unraid

I use the published container image directly, so I do not need a Git checkout
or Docker Compose on my Unraid server. The dashboard has no login. I bind port
`8787` only inside a trusted LAN and never expose it through a router port
forward.

## 1. I prepare persistent app data and configuration

I run this once in the Unraid terminal:

```bash
mkdir -p /mnt/user/appdata/paper-trading-bot/data
chown -R nobody:users /mnt/user/appdata/paper-trading-bot/data
chmod 775 /mnt/user/appdata/paper-trading-bot/data
touch /mnt/user/appdata/paper-trading-bot/.env
chown root:root /mnt/user/appdata/paper-trading-bot/.env
chmod 600 /mnt/user/appdata/paper-trading-bot/.env
```

I deliberately run the container without root privileges as UID/GID `99:100`.
These permissions allow SQLite to create and update the database without
weakening that runtime restriction.

I edit `/mnt/user/appdata/paper-trading-bot/.env` and start with the complete
[`.env.example`](../.env.example). These are the minimum values I verify:

```dotenv
PAPER_ONLY=true
APP_LANGUAGE=en
DATA_SOURCE=demo
FUSION_READ_API_KEY=
APP_TIMEZONE=Europe/Berlin
DATA_DIR=/data
```

I use `APP_LANGUAGE=en` or `APP_LANGUAGE=de` as the default dashboard language.
I keep the file owned by `root:root` with mode `600` because it can contain my
Fusion API key.

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

## 3. I create the container

Under **Docker → Add Container**, I enter:

| Field | My value |
| --- | --- |
| Name | `paper-trading-bot` |
| Repository | `ghcr.io/2crazytv/multi-coin-paper-daytrader:latest` |
| Network Type | `bridge` |
| WebUI | `http://[IP]:[PORT:8787]/` |
| Container Port | `8787` |
| Host Port | `8787` |
| Container Path | `/data` |
| Host Path | `/mnt/user/appdata/paper-trading-bot/data` |
| Access Mode | `Read/Write` |
| Container Variable | `TZ=Europe/Berlin` |

I add these **Extra Parameters**:

```text
--env-file=/mnt/user/appdata/paper-trading-bot/.env --user=99:100 --read-only --init --tmpfs=/tmp:size=64m,mode=1777 --security-opt=no-new-privileges:true --cap-drop=ALL --pids-limit=2048 --restart=unless-stopped --stop-timeout=20
```

The included
[`unraid/multi-coin-paper-daytrader.xml`](../unraid/multi-coin-paper-daytrader.xml)
already contains these values. It intentionally defines only the WebUI port,
the persistent data path, and the container timezone. I keep every application
setting in `.env`; adding the same application setting as an Unraid variable
would pass an explicit `-e` option and override the value from my `.env` file.

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

I use the language selector in the top bar to switch the complete dashboard
between English and German immediately. The browser stores my selection on that
device. For a new browser, `APP_LANGUAGE=en` or `APP_LANGUAGE=de` in `.env`
defines the initial language. A stored browser selection takes precedence over
that default.

Changing the selector does not restart the container and does not alter paper
trades, strategy rules, or market data. If I change `APP_LANGUAGE` in `.env`, I
select **Apply** or recreate the container so the new default reaches the app.

## 6. I enable read-only current market data

If I want current Fusion data, I set `DATA_SOURCE=fusion` and provide
`FUSION_READ_API_KEY`. I create that key with **Read** permission only and
leave **Trade** and **Transfer** disabled. I then select **Apply** so Unraid
recreates the container.

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
trades, and cached market snapshots, but it does not delete my `.env`, API key,
or container configuration.

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

### I receive `Permission denied` for `/data`

I repeat the ownership commands from section 1. I do not work around the problem
by running the container as root.

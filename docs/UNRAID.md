# Installation und Betrieb auf Unraid

Diese Anleitung verwendet das veröffentlichte Container-Image und benötigt
weder einen Git-Checkout noch Docker Compose. Das Dashboard besitzt keine
Anmeldung: Port `8787` nur im vertrauenswürdigen LAN freigeben und niemals
direkt per Router-Portfreigabe ins Internet veröffentlichen.

## 1. Appdata vorbereiten

Im Unraid-Terminal einmalig ausführen:

```bash
mkdir -p /mnt/user/appdata/paper-trading-bot/data
chown -R nobody:users /mnt/user/appdata/paper-trading-bot/data
chmod 775 /mnt/user/appdata/paper-trading-bot/data
```

Der Container läuft absichtlich ohne Root-Rechte als UID/GID `99:100`. Ohne
passende Rechte kann SQLite die Datenbank nicht erstellen oder aktualisieren.

## 2. Privates oder öffentliches Image abrufen

Solange das GHCR-Paket privat ist, benötigt Unraid einen klassischen GitHub-PAT
mit mindestens `read:packages`. Den Token niemals als Klartext in einen Befehl,
Chat oder eine Datei schreiben:

```bash
read -rsp 'GHCR-Token: ' GHCR_TOKEN
printf '\n'
printf '%s' "$GHCR_TOKEN" | \
  docker login ghcr.io -u 2CrAzYTV --password-stdin
unset GHCR_TOKEN
```

Nach einer späteren öffentlichen Freigabe ist für dieses Image kein Login mehr
nötig. Ein gespeicherter Login kann dann mit `docker logout ghcr.io` entfernt
werden.

## 3. Container in Unraid anlegen

Unter **Docker → Add Container** folgende Kernwerte setzen:

| Feld | Wert |
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

Unter **Extra Parameters** eintragen:

```text
--user=99:100 --read-only --init --tmpfs=/tmp:size=64m,mode=1777 --security-opt=no-new-privileges:true --cap-drop=ALL --restart=unless-stopped --stop-timeout=20
```

Die Umgebungsvariablen können auf zwei Arten gesetzt werden. Nicht beide
Methoden mischen.

### Variante A: Unraid-Felder

Die Datei [`unraid/multi-coin-paper-daytrader.xml`](../unraid/multi-coin-paper-daytrader.xml)
enthält alle empfohlenen Variablen als fertige Unraid-Template-Felder. Für eine
manuelle Anlage müssen mindestens diese Variablen gesetzt werden:

| Variable | Standardwert |
| --- | --- |
| `PAPER_ONLY` | `true` |
| `DATA_SOURCE` | `demo` |
| `DATA_DIR` | `/data` |
| `APP_TIMEZONE` | `Europe/Berlin` |
| `TZ` | `Europe/Berlin` |
| `PAIRS` | `BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR,ADA-EUR` |

Die übrigen Werte aus [`.env.example`](../.env.example) sind bereits sichere
Anwendungsstandards und können bei Bedarf als weitere Variablen hinzugefügt
werden.

### Variante B: lokale `.env`

Bestehende Installationen können stattdessen
`/mnt/user/appdata/paper-trading-bot/.env` verwenden. Dann zusätzlich unter
**Extra Parameters** vor den obigen Optionen eintragen:

```text
--env-file=/mnt/user/appdata/paper-trading-bot/.env
```

Die Datei schützen:

```bash
chown root:root /mnt/user/appdata/paper-trading-bot/.env
chmod 600 /mnt/user/appdata/paper-trading-bot/.env
```

## 4. Start prüfen

Nach **Apply** sollte Unraid den Container als `healthy` anzeigen. Zusätzlich:

```bash
docker inspect paper-trading-bot \
  --format 'Status={{.State.Status}} Health={{.State.Health.Status}} Image={{.Config.Image}}'
curl -fsS http://127.0.0.1:8787/health
docker logs --tail=50 paper-trading-bot
```

Erwartete Health-Antwort im Demo-Modus:

```json
{"status":"ok","paper_only":true,"data_source":"demo"}
```

Dashboard: `http://UNRAID-IP:8787`

## Echte, ausschließlich lesende Marktdaten

Für Fusion-Marktdaten `DATA_SOURCE=fusion` setzen und
`FUSION_READ_API_KEY` ergänzen. Der Schlüssel darf ausschließlich die
Berechtigung **Read** besitzen. **Trade** und **Transfer** müssen deaktiviert
bleiben. Nach der Änderung **Apply** wählen, damit Unraid den Container neu
erstellt.

## Updates

Ein neuer Commit auf `main` kann ein neues `:latest`-Image bauen. Der laufende
Container aktualisiert sich dadurch **nicht** selbst. Auch `docker restart` und
`--restart=unless-stopped` laden kein neues Image.

Während der Testphase wird ein kontrolliertes manuelles Update empfohlen:

1. Vorher ein Datenbank-Backup erstellen.
2. Unraid unter **Docker** öffnen und **Check for Updates** wählen.
3. Beim Container **Update** beziehungsweise **Force Update** ausführen.
4. Health, Logs und Dashboard erneut prüfen.

Unraid zieht das Image und erstellt den Container aus seiner gespeicherten
Vorlage neu. Der Bind-Mount `/mnt/user/appdata/paper-trading-bot/data` bleibt
dabei erhalten. Bei einem privaten Paket muss der GHCR-Login weiterhin gültig
sein. Ein unbeaufsichtigter Auto-Updater wird für die Erprobungsphase nicht
empfohlen.

## Backup und Wiederherstellung

Für ein konsistentes Backup den Container kurz stoppen:

```bash
docker stop paper-trading-bot
cp -a \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3 \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3.backup
docker start paper-trading-bot
```

Vor einem Update den bisherigen Digest notieren:

```bash
docker image inspect \
  ghcr.io/2crazytv/multi-coin-paper-daytrader:latest \
  --format '{{index .RepoDigests 0}}'
```

Für einen Rollback im Unraid-Template vorübergehend statt `:latest` die
vollständige Ausgabe mit `@sha256:…` als Repository verwenden und **Apply**
wählen. Tags wie `latest` sind veränderlich; ein Digest bezeichnet exakt ein
Image.

## Fehlerdiagnose

### `unauthorized` beim Pull

Das Paket ist noch privat oder der Token besitzt kein `read:packages`. Erneut
wie oben anmelden, ohne den Token in die Shell-Historie zu schreiben.

### Container läuft, WebUI öffnet nicht

```bash
docker ps --filter 'name=paper-trading-bot'
docker port paper-trading-bot
curl -I --max-time 5 http://127.0.0.1:8787/
curl -I --max-time 5 http://UNRAID-IP:8787/
```

Port `8787/tcp` muss auf `0.0.0.0:8787` oder die gewünschte LAN-Adresse
abgebildet sein. Zusätzlich Browser-Cache, lokale Firewall und VLAN-Regeln
prüfen.

### `Permission denied` für `/data`

Die Rechte aus Abschnitt 1 erneut setzen. Den Container nicht als Root starten,
um das Rechteproblem zu umgehen.

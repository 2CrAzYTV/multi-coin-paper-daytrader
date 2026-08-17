# Multi-Coin Paper Daytrader – Unraid Edition

Eine vollständig simulierte Daytrading-Umgebung für **1.000 € virtuelles
Startkapital**. Sie überwacht standardmäßig fünf liquide EUR-Kryptomärkte und
vergleicht drei Varianten unter denselben Marktbedingungen:

1. **Long-only, maximal 1× Exposition**
2. **Long/Short, maximal 1× Exposition**
3. **Long/Short, maximal 2× Exposition**

Standarduniversum: `BTC-EUR`, `ETH-EUR`, `SOL-EUR`, `XRP-EUR`, `ADA-EUR`.
Die 1.000 € gelten je Vergleichsstrategie als **ein gemeinsames Portfolio**,
nicht als zusätzliches Kapital pro Coin.

> **Veröffentlichungsstatus:** Repository und Container-Image befinden sich
> derzeit in einer privaten Erprobungsphase. Die technische Vorbereitung für
> eine spätere öffentliche MIT-Veröffentlichung ist vorhanden; die bewusste
> Freigabe erfolgt erst nach Abschluss der
> [Release-Checkliste](docs/RELEASE_CHECKLIST.md).

## Sicherheitsstatus

Diese Version ist technisch **Paper-only**:

- Es gibt im Programm keine Funktion zum Erstellen, Ändern, Stornieren oder
  Bestätigen echter Orders.
- Der Bitpanda-Client besitzt ausschließlich lesende `GET`-Marktdatenmethoden.
- `PAPER_ONLY=false` verhindert den Programmstart.
- Für echte Fusion-Daten genügt ein API-Key mit dem Scope **Read**. Die Scopes
  **Trade** und **Transfer** dürfen nicht aktiviert werden.
- Der Schlüssel bleibt nur in der lokalen `.env`, wird von Git ignoriert und
  niemals über das Dashboard ausgegeben.

Bitpanda beschreibt die Berechtigungen in der offiziellen
[Fusion-Key-Dokumentation](https://docs.fusion.bitpanda.com/api-key-generation-363384m0).

## Portfolioweite Risikoregeln

| Regel | Standard | Bedeutung bei 1.000 € |
| --- | ---: | ---: |
| Modelliertes Risiko je Trade | 0,5 % | höchstens ca. 5 € |
| Gesamtrisiko aller offenen Trades | 1 % | höchstens ca. 10 € |
| Tagesverlust-Limit | 2 % | höchstens ca. 20 € |
| Gleichzeitige Positionen | 2 | über alle Coins zusammen |
| Neue Trades pro Tag | 3 | über alle Coins zusammen |
| Dauerhafter Not-Aus | 10 % Drawdown | schließen und bis Reset sperren |
| Maximaler Hebel | 2× | nur in Vergleichsstrategie 3 |

Positionsgrößen berücksichtigen Stop-Abstand, Gebührenannahme und Slippage.
Kurslücken können auch in realen Märkten zu höheren Verlusten führen. Diese
Grenzen sind deshalb ein konservatives Modell und keine Verlustgarantie.

## Strategie

- Signalintervall: **15 Minuten**
- Trendfilter: **1 Stunde**
- Einstieg: frische EMA-9/EMA-21-Kreuzung in Richtung des 1-Stunden-Trends
- Filter: RSI und relatives Kerzenvolumen
- Stop: größerer Wert aus `1,5 × ATR(14)` und `0,6 %`
- Gewinnziel: `2R`
- Ab `1R` wird der Stop auf Einstand nachgezogen
- Nach einem Ausstieg gilt pro Coin eine 45-minütige Abkühlzeit
- Um 23:45 Uhr `Europe/Berlin` werden offene Positionen glattgestellt

Der Bot fragt die von Bitpanda als aktiv gemeldeten Paare ab und überspringt
nicht verfügbare Märkte. Die Fusion-Dokumentation stellt dafür lesende
[Paarlisten](https://docs.fusion.bitpanda.com/get-trading-pairs-4295528e0) und
[OHLCV-Kerzen](https://docs.fusion.bitpanda.com/get-candles-4311313e0) bereit.

## Warum noch keine Edelmetalle?

Gold und Silber sind als langfristige Diversifikation interessant, aber nicht
für dasselbe 15-Minuten-Regelwerk. Bitpanda nennt derzeit Kauf-/Verkaufsaufschläge
von zusammen etwa **1,5 % bei Gold** und **4,5 % bei Silber**. Das wäre im
Verhältnis zum 2-%-Tageslimit zu teuer. Quelle:
[Bitpanda Metals](https://support.bitpanda.com/hc/de/articles/360004208619-Was-ist-Bitpanda-Metals).

## Empfohlene Installation auf Unraid

Das fertige Image benötigt auf Unraid weder Git noch Docker Compose:

```text
ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
```

Die vollständige Schritt-für-Schritt-Anleitung enthält:

- private GHCR-Anmeldung und späteren öffentlichen Pull
- native **Add Container**-Felder und ein fertiges Unraid-XML-Template
- gehärtete Container-Optionen ohne Root-Rechte
- Start-, Health- und WebUI-Prüfung
- manuelle Updates, Backups und Rollback per Image-Digest
- Fehlerdiagnose für Pull, Rechte, Port und WebUI

➡️ **[Installation und Betrieb auf Unraid](docs/UNRAID.md)**

Das Dashboard ist anschließend unter `http://UNRAID-IP:8787` erreichbar. Es
besitzt keine Anmeldung und darf nur im vertrauenswürdigen LAN verfügbar sein.

## Installation aus dem Quellcode

Für Entwicklung oder lokale Builds kann das Repository weiterhin mit Docker
Compose gestartet werden:

```bash
git clone https://github.com/2CrAzYTV/multi-coin-paper-daytrader.git paper-trading-bot
cd paper-trading-bot
cp .env.example .env
mkdir -p data
chown -R nobody:users data
docker compose up -d --build
```

Dashboard öffnen:

```text
http://UNRAID-IP:8787
```

Status prüfen:

```bash
docker compose ps
docker compose logs --tail=100 paper-trading-bot
```

Der SQLite-Datenbestand liegt dauerhaft unter
`./data/paper_trading.sqlite3`. Die lokale `.env` bleibt bei Updates erhalten.

## Updates auf Unraid

Ein Push auf `main` kann ein neues `:latest`-Image erzeugen, ersetzt aber keinen
laufenden Container. `--restart=unless-stopped` startet nur dasselbe lokale
Image nach Absturz, Docker-Neustart oder Server-Reboot. Auch `docker restart`
führt keinen Pull aus.

Während der privaten Erprobung Updates deshalb kontrolliert über Unraid
ausführen: **Docker → Check for Updates → Update/Force Update**. Das Image wird
gezogen und der Container mit seinen gespeicherten Einstellungen neu erstellt.
Der `/data`-Bind-Mount bleibt erhalten. Für das private Paket muss Unraid bei
GHCR angemeldet sein.

Vor einem größeren Update ist ein Backup sinnvoll:

```bash
docker stop paper-trading-bot
cp -a \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3 \
  /mnt/user/appdata/paper-trading-bot/data/paper_trading.sqlite3.backup
docker start paper-trading-bot
```

Details und Rollback-Anleitung: [docs/UNRAID.md](docs/UNRAID.md#updates).

## Zuerst im Demo-Modus starten

Die mitgelieferte `.env.example` verwendet `DATA_SOURCE=demo`. Damit startet der Bot
sofort mit reproduzierbaren Offline-Daten. Für echte Bitpanda-Marktdaten:

1. In Bitpanda einen **Fusion API Key ausschließlich mit Read-Recht** anlegen.
2. Lokal in `.env` ändern:

   ```dotenv
   DATA_SOURCE=fusion
   FUSION_READ_API_KEY=DEIN_LOKALER_READ_KEY
   ```

3. Container neu erstellen:

   ```bash
   docker compose up -d --build
   ```

Den Schlüssel niemals committen, veröffentlichen oder im Chat teilen.

## Bedienung

- **Jetzt prüfen:** Holt die letzte geschlossene Kerze. Dieselbe Kerze wird
  nicht doppelt verarbeitet.
- **Multi-Coin-Backtest:** Simuliert alle Paare mit gemeinsamem Risikobudget;
  er verändert die laufenden Paper-Konten nicht.
- **Paper-Daten löschen:** Setzt ausschließlich die lokale Simulation zurück.

Der Scheduler prüft standardmäßig alle 60 Sekunden, handelt aber höchstens bei
einer **neuen geschlossenen 15-Minuten-Kerze**. Ein Signal führt nicht
automatisch zu einem Trade. In ruhigen Phasen sind null Trades pro Tag normal;
durch die globale Begrenzung sind maximal drei neue Einstiege pro Tag möglich.

## Konfiguration

Alle Einstellungen stehen in `.env`. Die wichtigsten Grenzen sind zusätzlich
im Code hart begrenzt:

- `RISK_PER_TRADE` maximal `0.01`
- `MAX_AGGREGATE_RISK` maximal `0.02`
- `MAX_DAILY_LOSS` maximal `0.02`
- `MAX_OPEN_POSITIONS` maximal `3`
- `MAX_TRADES_PER_DAY` maximal `6`
- `PAPER_ONLY` muss `true` bleiben

## Tests

```bash
python -m unittest discover -s tests -v
```

Zusätzliche lokale Prüfungen:

```bash
python -m compileall -q app tests
node --check app/static/app.js
python -c "import xml.etree.ElementTree as ET; ET.parse('unraid/multi-coin-paper-daytrader.xml')"
```

## Grenzen

- Das Projekt verspricht keine Rendite und ersetzt keinen Nebenjob planbar.
- Ein Backtest kann durch Überanpassung und kurze Historie irreführend sein.
- Gebühren sind konfigurierbare Annahmen und müssen regelmäßig mit dem eigenen
  Bitpanda-Konditionsmodell verglichen werden.
- Krypto-Assets sind stark korreliert; mehrere Coins bedeuten nicht automatisch
  echte Diversifikation.
- Steuern werden nicht berechnet.
- Ein stabiler Paper-Test über mehrere Marktphasen ist Voraussetzung für jede
  spätere Entscheidung. Echtgeldhandel ist bewusst nicht Bestandteil dieses
  Repositories.

## Lizenz, Sicherheit und Mitwirkung

- [MIT-Lizenz](LICENSE)
- [Haftungsausschluss](DISCLAIMER.md)
- [Sicherheitsrichtlinie](SECURITY.md)
- [Support](SUPPORT.md)
- [Beitragsrichtlinien](CONTRIBUTING.md)
- [Verhaltenskodex](CODE_OF_CONDUCT.md)
- [Checkliste für die öffentliche Veröffentlichung](docs/RELEASE_CHECKLIST.md)

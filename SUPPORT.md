# Support

Vor einer Anfrage bitte die [Unraid-Anleitung](docs/UNRAID.md), vorhandene
Issues und die Container-Logs prüfen.

Für reproduzierbare Fehler und konkrete Verbesserungsvorschläge stehen die
[GitHub-Issues](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/issues)
zur Verfügung. Allgemeine Finanz-, Anlage- oder Steuerberatung gehört nicht zum
Supportumfang.

In einem Fehlerbericht dürfen keine `.env`, API-Schlüssel, Registry-Tokens oder
vollständigen Datenbanken enthalten sein. Geeignete Diagnoseinformationen sind:

```bash
docker inspect paper-trading-bot \
  --format 'Image={{.Config.Image}} Status={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker logs --tail=100 paper-trading-bot
```

Vor dem Veröffentlichen die Ausgabe auf Geheimnisse und persönliche Daten
prüfen. Sicherheitsprobleme bitte ausschließlich nach [SECURITY.md](SECURITY.md)
melden.

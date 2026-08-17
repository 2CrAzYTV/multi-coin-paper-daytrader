# Mitwirken

Beiträge zu Fehlerbehebungen, Dokumentation, Tests und neuen Paper-Strategien
sind willkommen. Bitte vor größeren Änderungen zuerst ein Issue anlegen, damit
Ziel und Sicherheitsfolgen abgestimmt werden können.

## Unveränderliche Sicherheitsgrenzen

Ein Beitrag darf diese Regeln nicht aufweichen:

- keine Methoden zum Erstellen, Ändern, Stornieren oder Bestätigen echter Orders
- keine Konto-, Einzahlungs-, Auszahlungs- oder Transferfunktionen
- externe Börsenkommunikation ausschließlich lesend
- `PAPER_ONLY=false` muss den Programmstart weiterhin verhindern
- API-Schlüssel und andere Geheimnisse dürfen weder geloggt noch ausgeliefert
  oder in Tests eingebettet werden
- bestehende harte Risikoobergrenzen dürfen nicht still erhöht werden
- das Dashboard darf nicht als öffentlich authentifizierter Dienst dargestellt
  werden; es besitzt keine Anmeldung

## Lokale Entwicklung

Python 3.12 und Node.js werden für die gleichen Prüfungen wie in CI benötigt:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check app/static/app.js
```

Das Container-Image lässt sich anschließend lokal prüfen:

```bash
docker build --pull -t multi-coin-paper-daytrader:test .
```

## Pull Requests

- Einen kurzen, sachlichen Titel und eine nachvollziehbare Beschreibung nutzen.
- Verhaltensänderungen mit Tests und Benutzerdokumentation ergänzen.
- Keine generierten Datenbanken, `.env`, Tokens oder persönlichen Marktdaten
  einchecken.
- Die Checkliste in der Pull-Request-Vorlage vollständig prüfen.
- Änderungen am Verhalten im Abschnitt `Unreleased` von `CHANGELOG.md`
  dokumentieren.

Mit einem Beitrag erklärst du dich damit einverstanden, ihn unter der
[MIT-Lizenz](LICENSE) des Projekts bereitzustellen.

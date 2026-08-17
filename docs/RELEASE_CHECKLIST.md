# Checkliste für die erste öffentliche Veröffentlichung

Diese Liste ist für die geplante Umstellung von privater Erprobung auf eine
öffentliche MIT-Veröffentlichung gedacht. Ein öffentliches GHCR-Paket kann laut
GitHub anschließend nicht wieder auf privat zurückgestellt werden. Diesen
Schritt deshalb erst nach bewusstem Abschluss der Testphase ausführen.

## 1. Erprobung abschließen

- [ ] Mindestens 3–7 Tage stabiler Dauerbetrieb auf Unraid
- [ ] Health-Status dauerhaft `healthy`; keine ungeklärten Neustarts
- [ ] Dashboard, manueller Paper-Lauf und Multi-Coin-Backtest geprüft
- [ ] Tagesabschluss und Neustart mit offenen beziehungsweise geschlossenen
      Paper-Positionen beobachtet
- [ ] SQLite-Daten bleiben nach Neustart und Image-Neuerstellung erhalten
- [ ] Demo-Modus geprüft
- [ ] Optionaler Fusion-Modus ausschließlich mit einem Read-only-Key geprüft
- [ ] Keine echte Order-, Konto-, Trade- oder Transferfunktion vorhanden

## 2. Repository prüfen

- [ ] CI auf `main` vollständig grün
- [ ] `python -m unittest discover -s tests -v` erfolgreich
- [ ] `python -m compileall -q app tests` erfolgreich
- [ ] `node --check app/static/app.js` erfolgreich
- [ ] Unraid-XML ist wohlgeformt und enthält das korrekte Image
- [ ] README, Unraid-Anleitung und Changelog entsprechen dem Release
- [ ] MIT-Lizenz, Haftungsausschluss, Security- und Beitragsrichtlinien geprüft
- [ ] Gesamten Git-Verlauf auf `.env`, PATs, API-Schlüssel, Datenbanken und
      persönliche Informationen prüfen
- [ ] GitHub Secret Scanning und Dependabot aktiv beziehungsweise grün
- [ ] Offene Sicherheits- und Blocker-Issues geklärt

## 3. Container prüfen

- [ ] Image auf sauberem `linux/amd64`-Host neu ziehen und starten
- [ ] Container läuft als `99:100`, read-only, ohne Capabilities und mit
      `no-new-privileges`
- [ ] `/data` ist der einzige dauerhaft beschreibbare Bind-Mount
- [ ] Health-Endpunkt meldet `paper_only: true`
- [ ] Aktuellen funktionierenden Digest und Datenbank-Backup notieren
- [ ] Rollback auf den vorherigen Digest einmal getestet

## 4. Sichtbarkeit bewusst umstellen

- [ ] Repository-Inhaber bestätigt ausdrücklich die Veröffentlichung
- [ ] GitHub-Repository von **Private** auf **Public** stellen
- [ ] Repository anonym beziehungsweise abgemeldet öffnen und Dokumentation
      sowie Lizenz prüfen
- [ ] GHCR-Paket erst danach bewusst von **Private** auf **Public** stellen
- [ ] Warnung bestätigen: Das öffentliche Paket kann nicht wieder privat werden
- [ ] Abgemeldet testen:

  ```bash
  docker logout ghcr.io
  docker pull ghcr.io/2crazytv/multi-coin-paper-daytrader:latest
  ```

- [ ] Keine privaten Quellarchive, Backups oder Tokens als Artefakt enthalten

## 5. Release erstellen

- [ ] `Unreleased`-Änderungen in eine Versionssektion mit Datum verschieben
- [ ] Version in Anwendung und Docker-Label synchronisieren
- [ ] Signierten oder geschützten Tag im Format `vX.Y.Z` erstellen
- [ ] GitHub Actions für Tag und Image erfolgreich
- [ ] Release Notes mit Funktionen, Sicherheitsgrenzen, Upgrade- und
      Rollback-Hinweisen veröffentlichen
- [ ] Versionstag und Digest dokumentieren

## 6. Nachbereitung

- [ ] Nicht mehr benötigte PATs und temporäre Deploy Keys widerrufen
- [ ] Lokale Registry-Anmeldedaten entfernen, wenn öffentlicher Pull genügt
- [ ] Öffentliche Installation anhand `docs/UNRAID.md` auf einem sauberen System
      nachvollziehen
- [ ] Erst nach erfolgreicher öffentlicher Installation eine Einreichung bei
      Unraid Community Applications erwägen
- [ ] Sicherheitsmeldungen und Dependency-Updates regelmäßig prüfen

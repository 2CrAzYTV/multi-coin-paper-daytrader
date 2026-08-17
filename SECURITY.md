# Sicherheitsrichtlinie

## Unterstützte Versionen

Sicherheitskorrekturen werden für den aktuellen Stand von `main` und den
neuesten veröffentlichten Versions-Tag vorbereitet. Ältere Tags erhalten
grundsätzlich keine separaten Backports.

## Schwachstellen vertraulich melden

Bitte keine Zugangsdaten, API-Schlüssel, Datenbankinhalte oder noch nicht
behobenen Schwachstellen in ein öffentliches Issue schreiben.

1. Wenn im GitHub-Tab **Security** die Funktion **Report a vulnerability**
   angeboten wird, darüber einen privaten Bericht erstellen.
2. Falls die Funktion nicht verfügbar ist, ein Issue ohne technische Details
   mit dem Titel `Security contact requested` eröffnen. Der Repository-Inhaber
   stellt anschließend einen privaten Kommunikationsweg bereit.

Hilfreich sind betroffene Version, reproduzierbare Schritte, Auswirkung und ein
möglicher Fix. Zugangsdaten müssen immer entfernt oder durch Platzhalter ersetzt
werden.

## Sicherheitsmodell

- Die Anwendung muss mit `PAPER_ONLY=true` laufen; `false` verhindert den Start.
- Der Marktdaten-Client darf ausschließlich lesende Endpunkte verwenden.
- Ein optionaler Fusion-Schlüssel darf nur das Recht **Read**, niemals **Trade**
  oder **Transfer**, besitzen.
- Das Dashboard besitzt keine Benutzeranmeldung. Es ist ausschließlich für ein
  vertrauenswürdiges LAN oder ein vorgeschaltetes, abgesichertes Gateway
  vorgesehen und darf nicht direkt ins Internet veröffentlicht werden.
- `.env`, Datenbanken, Backups und Registry-Tokens gehören nicht ins Repository
  und nicht in Fehlerberichte.

Eine Anleitung zum gehärteten Betrieb steht in [docs/UNRAID.md](docs/UNRAID.md).

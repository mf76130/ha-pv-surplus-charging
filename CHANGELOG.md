# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [1.4.0] - 2026-08-09

### Hinzugefügt
- 🔌 **Anschluss-Erkennung vor dem Start**: Neues Feld "Zustände ohne Auto" (Standard: `idle,sleep,fault`) verhindert, dass der Start-Button gedrückt wird, wenn laut Ladestatus-Sensor gar kein Auto angeschlossen ist. Verhindert unnötige/wirkungslose Start-Versuche bei ausreichendem PV-Überschuss ohne angestecktes Fahrzeug.

## [1.3.0] - 2026-08-09

### Hinzugefügt
- 🔋 **Pro-Auto Mindest-Ladestrom**: Jedes Auto kann jetzt einen eigenen minimalen Ladestrom hinterlegen (z. B. 13A für Fahrzeuge, die unterhalb eines bestimmten Stroms gar nicht erst zu laden anfangen). Überschreibt den globalen Mindest-Ladestrom, sobald dieses Auto aktiv ausgewählt ist. Fehlt der Wert bei einem Auto, gilt weiterhin der globale Standardwert.

## [1.2.0] - 2026-08-09

### Hinzugefügt
- ✏️ Neuer Menüpunkt **"Auto bearbeiten"** unter "Autos verwalten" – bestehende Autos (Name, Ladestand-Sensor, Standard-Ziel-Ladestand) lassen sich jetzt nachträglich ändern, ohne sie erst entfernen und neu anlegen zu müssen.

## [1.1.0] - 2026-08-08

### Hinzugefügt
- 🚗 **Unterstützung für mehrere Autos** – beliebig viele Fahrzeuge lassen sich anlegen, jedes mit eigenem Ladestand-Sensor und Standard-Ziel-Ladestand.
- 🔀 Neue Entität `select.aktuelles_auto` – legt fest, welches Auto gerade an der (mobilen) Wallbox lädt. Ohne Auswahl pausiert die Automatik.
- 🎯 Neue Entität `number.ziel_ladestand` – zeigt den Ziel-Ladestand des aktiven Autos an und lässt sich jederzeit manuell anpassen; springt bei Autowechsel automatisch auf den hinterlegten Standardwert zurück.
- 🛑 Ladevorgang wird automatisch gestoppt, sobald der Ladestand des aktiven Autos den Ziel-Ladestand erreicht – unabhängig vom PV-Überschuss.
- 🧭 Neuer Menüpunkt **"Autos verwalten"** in den Integrations-Optionen zum nachträglichen Hinzufügen/Entfernen von Fahrzeugen.
- 🔍 Entity-Filter im Einrichtungsdialog: Auswahlfelder zeigen nur noch passende Entitäten an (`device_class: current` für Ladestrom, `power` für Netzleistung, `battery` für Fahrzeug-Ladestand).

### Geändert
- Options-Flow umstrukturiert: getrennte Menüpunkte für "Regelparameter ändern" und "Autos verwalten".
- Versionsnummer der Integration auf `1.1.0` angehoben.

## [1.0.0] - 2026-08-08

### Hinzugefügt
- 🎉 Erste Version der PV-Überschussladesteuerung als HACS-installierbare Custom Integration.
- ⚙️ Config-Flow mit freier Auswahl aller benötigten Entitäten (Ladestrom, Ladestatus, Start-/Stop-Button, Netzleistung) – funktioniert damit mit beliebigen Wallboxen, nicht nur einem festen Modell.
- 📉 Automatische Regelung des Ladestroms anhand der Netzleistung: reduziert bei Netzbezug, erhöht bei Überschuss, gerundet auf konfigurierbare Schrittweite.
- ⏱️ Konfigurierbare Start-/Stoppverzögerung, um Takten bei kurzzeitigen Einstrahlungsschwankungen zu vermeiden.
- 🔌 Neue Entität `switch.pv_uberschussladen_aktiv` zum vollständigen Ein-/Ausschalten der Automatik, Zustand bleibt über Neustarts erhalten.
- 🛠️ Options-Flow zum nachträglichen Anpassen aller Entitäten und Regelparameter ohne Neueinrichtung.

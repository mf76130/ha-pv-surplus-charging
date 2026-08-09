# PV Surplus Charging (PV-Überschussladesteuerung)

> Siehe [CHANGELOG.md](CHANGELOG.md) für die Versionshistorie.

Home Assistant Custom Integration zur PV-Überschussladung einer mobilen Wallbox, deren Entitäten frei im Config-Flow ausgewählt werden können. Es ist also **kein** fest verdrahteter Support für ein bestimmtes Wallbox-Modell nötig – jede Wallbox mit `number`-Entität für den Ladestrom, `sensor`-Entität für den Status sowie `button`-Entitäten zum Starten/Stoppen funktioniert.

## Funktionsweise

Alle X Sekunden (konfigurierbares Regelintervall) wird die aktuelle Netzleistung (Hausanschluss) ausgelesen:

- **Positiver Wert** → Strom wird zugekauft. Der Ladestrom wird reduziert, bis die Netzleistung auf den konfigurierten Zielwert sinkt (Standard: **-100 W**, also ein kleiner Überschuss/Einspeisung).
- **Negativer Wert** (unter dem Zielwert) → Es ist Überschuss vorhanden. Der Ladestrom wird entsprechend erhöht.

Berechnung:

```
delta_power   = netzleistung - zielwert
delta_current = delta_power / (spannung * phasen)
neuer_strom   = aktueller_strom - delta_current   (auf Schrittweite gerundet, min/max begrenzt)
```

- Reicht der Überschuss nicht für den **minimalen Ladestrom**, wird die Ladung nach einer konfigurierbaren **Stoppverzögerung** über den Stop-Button beendet (verhindert Flackern bei kurzen Einbrüchen).
- Ist wieder ausreichend Überschuss vorhanden, wird nach einer konfigurierbaren **Startverzögerung** über den Start-Button neu gestartet.
- Während des Ladens wird der Ladestrom laufend nachgeregelt.

Ein eigener **Schalter (`switch.pv_uberschussladen_aktiv`)** erlaubt es, die automatische Regelung komplett ein-/auszuschalten, ohne die Integration zu entfernen. Der Zustand des Schalters bleibt über Neustarts erhalten.

### Mehrere Autos & Ziel-Ladestand

Da es sich um eine **mobile Wallbox** handelt, lassen sich beliebig viele Autos anlegen. Für jedes Auto hinterlegst du:

- einen **Ladestand-Sensor** aus Home Assistant (z. B. von der Fahrzeug-Integration, Einheit %)
- einen **Standard-Ziel-Ladestand** (z. B. 80 %)

Zwei zusätzliche Entitäten steuern den laufenden Betrieb:

- **`select.aktuelles_auto`** – hier legst du fest, welches Auto gerade an der Wallbox lädt. Erst wenn hier ein Auto gewählt ist, regelt die Automatik.
- **`number.ziel_ladestand`** – zeigt den Ziel-Ladestand des gewählten Autos an (Standardwert aus der Auto-Konfiguration) und kann jederzeit manuell übersteuert werden. Beim Wechsel des Autos wird automatisch wieder der hinterlegte Standardwert übernommen.

Sobald der Ladestand des aktiven Autos den Zielwert erreicht oder überschreitet, wird der Ladevorgang automatisch gestoppt – unabhängig vom PV-Überschuss.

### Entity-Filter beim Einrichten

Damit du nicht versehentlich die falsche Entität wählst, filtert der Config-Flow die Auswahl nach `device_class`:

- Ladestrom-Entität → nur `number`-Entitäten mit `device_class: current` (Einheit A)
- Netzleistungs-Entität → nur `sensor`-Entitäten mit `device_class: power` (Einheit W)
- Ladestand-Entität der Autos → nur `sensor`-Entitäten mit `device_class: battery` (Einheit %)

Falls deine gewünschte Entität nicht auftaucht, hat sie vermutlich keine passende `device_class` gesetzt – prüfe das in den Entitätseinstellungen (**Einstellungen → Entitäten → deine Entität → Zahnrad**) bzw. weise ihr über einen Template-Sensor die passende `device_class`/Einheit zu.

## Installation über HACS

1. In HACS auf die drei Punkte oben rechts klicken → **"Benutzerdefinierte Repositories"**.
2. `https://github.com/mf76130/pv-surplus-charging` eintragen, Kategorie **"Integration"** wählen.
3. "PV Surplus Charging" installieren und Home Assistant neu starten.

*(Voraussetzung: der Inhalt dieses Ordners liegt als Repo unter `github.com/mf76130/pv-surplus-charging`. Falls noch nicht geschehen: neues GitHub-Repository mit genau diesem Namen anlegen und den Inhalt dieses Ordners hineinpushen.)*

### Manuelle Installation (Alternative ohne HACS)

Den Ordner `custom_components/pv_surplus_charging` in das Verzeichnis `custom_components` deiner Home-Assistant-Konfiguration kopieren und Home Assistant neu starten.

## Einrichtung

**Einstellungen → Geräte & Dienste → Integration hinzufügen → "PV Surplus Charging"**

Im Config-Flow wählst du per Entity-Picker aus, welche Entitäten deiner Wallbox verwendet werden sollen, z. B.:

| Feld | Beispiel |
|---|---|
| Ladestrom (number) | `number.de_ev_charger_charge_current` |
| Ladestatus (sensor) | `sensor.de_ev_charger_status` |
| Button: Laden starten | `button.de_ev_charger_charge` |
| Button: Laden stoppen | `button.de_ev_charger_stop` |
| Netzleistung / Hausanschluss (sensor) | `sensor.leistung_alle_phasen` |

Zusätzlich konfigurierbar:

- **Status-Wert für „lädt“** – der exakte Zustandstext deines Status-Sensors, der "wird gerade geladen" bedeutet (z. B. `charging`). Wird verwendet, um zu entscheiden, ob Start-/Stop-Button gedrückt werden müssen.
- **Ziel-Netzleistung (W)** – Standard `-100`
- **Min./Max. Ladestrom (A)** – Standard `6` / `16`
- **Schrittweite (A)** – Standard `1`
- **Spannung (V)** – Standard `230`
- **Phasen** – `1` oder `3`, Standard `3`
- **Regelintervall (s)** – Standard `30`
- **Start-/Stoppverzögerung (s)** – Standard je `60`

Alle Werte lassen sich später über **Konfigurieren** an der Integration jederzeit anpassen (Options-Flow), auch die gewählten Entitäten.

## Entitäten, die die Integration anlegt

- `switch.<name>_pv_uberschussladen_aktiv` – Ein-/Ausschalter der Automatik
- `select.<name>_aktuelles_auto` – Auswahl, welches Auto gerade lädt
- `number.<name>_ziel_ladestand` – Ziel-Ladestand (%) des gewählten Autos

Alles andere (Ladestrom, Status, Buttons, Netzleistung, Fahrzeug-Ladestand) sind deine eigenen, bereits vorhandenen Entitäten – die Integration steuert sie nur an, legt aber keine Duplikate an.

## Autos nachträglich verwalten

**Konfigurieren** an der Integration → **"Autos verwalten"** → Auto hinzufügen / **bearbeiten** / entfernen. Über **"Regelparameter ändern"** lassen sich alle anderen Einstellungen (Entitäten, Ziel-Netzleistung, Verzögerungen etc.) jederzeit anpassen.

## Hinweise

- Diese Integration ersetzt keine Wallbox-Absicherung – die Grenzen (min/max Ladestrom) sollten zur Spezifikation deiner Wallbox passen.
- Bei sehr volatiler PV-Erzeugung (z. B. durchziehende Wolken) hilft ein größeres Regelintervall bzw. größere Start-/Stoppverzögerung, um unnötiges Takten zu vermeiden.

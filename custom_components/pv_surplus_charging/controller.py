"""Regel-Logik für die PV-Überschussladung."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_CAR_MIN_CURRENT,
    CONF_CAR_NAME,
    CONF_CAR_SOC_ENTITY,
    CONF_CAR_TARGET_SOC,
    CONF_CARS,
    CONF_CHARGE_CURRENT_ENTITY,
    CONF_CHARGING_STATE_VALUE,
    CONF_CURRENT_STEP,
    CONF_GRID_POWER_ENTITY,
    CONF_MAX_CURRENT,
    CONF_MIN_CURRENT,
    CONF_NOT_CONNECTED_STATES,
    CONF_PHASES,
    CONF_PV_POWER_ENTITY,
    CONF_START_BUTTON_ENTITY,
    CONF_START_DELAY,
    CONF_STATUS_ENTITY,
    CONF_STOP_BUTTON_ENTITY,
    CONF_STOP_DELAY,
    CONF_TARGET_GRID_POWER,
    CONF_UPDATE_INTERVAL,
    CONF_VOLTAGE,
    DEFAULT_CHARGING_STATE_VALUE,
    DEFAULT_CURRENT_STEP,
    DEFAULT_MAX_CURRENT,
    DEFAULT_MIN_CURRENT,
    DEFAULT_NOT_CONNECTED_STATES,
    DEFAULT_PHASES,
    DEFAULT_START_DELAY,
    DEFAULT_STOP_DELAY,
    DEFAULT_TARGET_GRID_POWER,
    DEFAULT_TARGET_SOC,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VOLTAGE,
    signal_car_changed,
)

_LOGGER = logging.getLogger(__name__)

UNAVAILABLE_STATES = ("unknown", "unavailable", None)


class PVSurplusChargingManager:
    """Verwaltet die periodische Regelung für einen konfigurierten Wallbox-Eintrag."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.enabled = True
        self.active_car_name: str | None = None
        self.target_soc: float = DEFAULT_TARGET_SOC
        self._unsub_timer = None
        self._below_min_seconds = 0
        self._above_min_seconds = 0
        self._last_setpoint: float | None = None

    @property
    def data(self) -> dict:
        """Konfiguration: Basisdaten + evtl. später über Options geänderte Werte."""
        merged = dict(self.entry.data)
        merged.update(self.entry.options)
        return merged

    def get_cars(self) -> list[dict]:
        """Liste der konfigurierten Autos."""
        return self.data.get(CONF_CARS, [])

    def get_car(self, name: str | None) -> dict | None:
        """Konfiguration eines Autos anhand des Namens."""
        if not name:
            return None
        for car in self.get_cars():
            if car[CONF_CAR_NAME] == name:
                return car
        return None

    def set_active_car(self, name: str | None) -> None:
        """Setzt das aktuell zu ladende Auto und dessen Standard-Zielladestand."""
        self.active_car_name = name
        car = self.get_car(name)
        self.target_soc = car[CONF_CAR_TARGET_SOC] if car else DEFAULT_TARGET_SOC
        self.reset_counters()
        async_dispatcher_send(self.hass, signal_car_changed(self.entry.entry_id))

    def set_target_soc(self, value: float) -> None:
        """Setzt den Ziel-Ladestand manuell (überschreibt den Auto-Standardwert)."""
        self.target_soc = value

    def start(self) -> None:
        interval = self.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self._unsub_timer = async_track_time_interval(
            self.hass, self._async_tick, timedelta(seconds=interval)
        )
        _LOGGER.debug("PV-Überschussladung gestartet, Intervall=%ss", interval)

    def stop(self) -> None:
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    def reset_counters(self) -> None:
        self._below_min_seconds = 0
        self._above_min_seconds = 0
        self._last_setpoint = None

    async def _async_tick(self, now) -> None:
        if not self.enabled:
            return
        try:
            await self.async_regulate()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Fehler bei der PV-Überschussladung-Regelung")

    async def async_regulate(self) -> None:
        hass = self.hass
        data = self.data

        grid_power_state = hass.states.get(data[CONF_GRID_POWER_ENTITY])
        current_state = hass.states.get(data[CONF_CHARGE_CURRENT_ENTITY])
        status_state = hass.states.get(data[CONF_STATUS_ENTITY])

        if grid_power_state is None or grid_power_state.state in UNAVAILABLE_STATES:
            _LOGGER.debug("Netzleistungs-Sensor nicht verfügbar, überspringe Zyklus")
            return

        try:
            grid_power = float(grid_power_state.state)
        except ValueError:
            _LOGGER.warning(
                "Netzleistungswert konnte nicht gelesen werden: %s", grid_power_state.state
            )
            return

        # PV-Leistung lesen: Laden darf nur beginnen, wenn die PV selbst
        # genug liefert. Damit wird verhindert, dass nächtliche
        # Batterie-Einspeisung (z. B. Marstek-Akkus) als Überschuss fehlinterpretiert wird.
        pv_power_state = hass.states.get(data.get(CONF_PV_POWER_ENTITY))
        pv_power = 0.0
        if pv_power_state is not None and pv_power_state.state not in UNAVAILABLE_STATES:
            try:
                pv_power = float(pv_power_state.state)
            except ValueError:
                _LOGGER.warning(
                    "PV-Leistung konnte nicht gelesen werden: %s", pv_power_state.state
                )
                pv_power = 0.0

        charging_value = data.get(CONF_CHARGING_STATE_VALUE, DEFAULT_CHARGING_STATE_VALUE)
        is_charging = bool(status_state and status_state.state == charging_value)

        not_connected_states = {
            s.strip()
            for s in data.get(CONF_NOT_CONNECTED_STATES, DEFAULT_NOT_CONNECTED_STATES).split(",")
            if s.strip()
        }
        is_connected = bool(status_state) and status_state.state not in not_connected_states

        # Kein Auto ausgewählt -> keine automatische Regelung möglich.
        active_car = self.get_car(self.active_car_name)
        if active_car is None:
            _LOGGER.debug("Kein Auto ausgewählt, PV-Überschussladung pausiert")
            return

        # Ziel-Ladestand des aktiven Autos prüfen, sofern der Sensor verfügbar ist.
        soc_state = hass.states.get(active_car[CONF_CAR_SOC_ENTITY])
        current_soc = None
        if soc_state is not None and soc_state.state not in UNAVAILABLE_STATES:
            try:
                current_soc = float(soc_state.state)
            except ValueError:
                _LOGGER.warning(
                    "Ladestand von %s konnte nicht gelesen werden: %s",
                    active_car[CONF_CAR_NAME],
                    soc_state.state,
                )

        if current_soc is not None and current_soc >= self.target_soc:
            if is_charging:
                _LOGGER.info(
                    "%s hat den Ziel-Ladestand von %s%% erreicht (%s%%), stoppe Ladevorgang",
                    active_car[CONF_CAR_NAME],
                    self.target_soc,
                    current_soc,
                )
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": data[CONF_STOP_BUTTON_ENTITY]},
                    blocking=True,
                )
            self.reset_counters()
            return

        min_current = active_car.get(
            CONF_CAR_MIN_CURRENT, data.get(CONF_MIN_CURRENT, DEFAULT_MIN_CURRENT)
        )
        max_current = data.get(CONF_MAX_CURRENT, DEFAULT_MAX_CURRENT)
        step = data.get(CONF_CURRENT_STEP, DEFAULT_CURRENT_STEP)
        voltage = data.get(CONF_VOLTAGE, DEFAULT_VOLTAGE)
        phases = data.get(CONF_PHASES, DEFAULT_PHASES)
        target = data.get(CONF_TARGET_GRID_POWER, DEFAULT_TARGET_GRID_POWER)
        interval = data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        start_delay = data.get(CONF_START_DELAY, DEFAULT_START_DELAY)
        stop_delay = data.get(CONF_STOP_DELAY, DEFAULT_STOP_DELAY)

        # Mindest-Ladeleistung, die der Überschuss/PV bereitstellen muss.
        min_charge_power = min_current * voltage * phases
        pv_ok = pv_power >= min_charge_power

        try:
            current_amp = (
                float(current_state.state)
                if current_state and current_state.state not in UNAVAILABLE_STATES
                else min_current
            )
        except ValueError:
            current_amp = min_current

        # Positive Netzleistung = Strom wird zugekauft -> Ladeleistung reduzieren.
        # Negative Netzleistung = Überschuss -> Ladeleistung erhöhen.
        delta_power = grid_power - target
        delta_current = delta_power / (voltage * phases)
        raw_new_current = current_amp - delta_current

        new_current = round(raw_new_current / step) * step
        new_current = max(min_current, min(max_current, new_current))

        # Regelung nur "freigeben", wenn Überschuss UND ausreichende PV-Leistung
        # anliegen. Fällt die PV weg (Nacht), zählt das sofort als Unterschuss.
        surplus_ok = raw_new_current >= min_current and pv_ok

        if not surplus_ok:
            self._below_min_seconds += interval
            self._above_min_seconds = 0
        else:
            self._above_min_seconds += interval
            self._below_min_seconds = 0

        # Nicht genug Überschuss oder keine PV-Leistung -> irgendwann stoppen
        if raw_new_current < min_current or not pv_ok:
            if is_charging and self._below_min_seconds >= stop_delay:
                reason = (
                    "keine PV-Leistung mehr (%.0f W)" % pv_power
                    if not pv_ok
                    else "zu wenig PV-Überschuss (Netz: %.0f W)" % grid_power
                )
                _LOGGER.info("%s, stoppe Ladevorgang", reason)
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": data[CONF_STOP_BUTTON_ENTITY]},
                    blocking=True,
                )
                self._last_setpoint = None
            return

        # Genug Überschuss -> ggf. starten (nur wenn wirklich ein Auto angeschlossen ist)
        if not is_charging:
            if not is_connected:
                _LOGGER.debug(
                    "Kein Auto angeschlossen (Status: %s), starte nicht",
                    status_state.state if status_state else "unbekannt",
                )
                return
            if self._above_min_seconds >= start_delay:
                _LOGGER.info(
                    "Ausreichend PV-Überschuss (Netz: %.0f W, PV: %.0f W), starte Ladevorgang für %s bei %s A",
                    grid_power,
                    pv_power,
                    active_car[CONF_CAR_NAME],
                    new_current,
                )
                await hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": data[CONF_CHARGE_CURRENT_ENTITY], "value": new_current},
                    blocking=True,
                )
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": data[CONF_START_BUTTON_ENTITY]},
                    blocking=True,
                )
                self._last_setpoint = new_current
            return

        # Bereits am Laden -> Ladestrom nachregeln, falls nötig
        if self._last_setpoint != new_current:
            _LOGGER.debug(
                "Setze Ladestrom auf %s A (Netz: %.0f W, PV: %.0f W, Ziel: %s W)",
                new_current,
                grid_power,
                pv_power,
                target,
            )
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": data[CONF_CHARGE_CURRENT_ENTITY], "value": new_current},
                blocking=True,
            )
            self._last_setpoint = new_current

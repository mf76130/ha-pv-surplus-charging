"""Regel-Logik für die PV-Überschussladung."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_CHARGE_CURRENT_ENTITY,
    CONF_CHARGING_STATE_VALUE,
    CONF_CURRENT_STEP,
    CONF_GRID_POWER_ENTITY,
    CONF_MAX_CURRENT,
    CONF_MIN_CURRENT,
    CONF_PHASES,
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
    DEFAULT_PHASES,
    DEFAULT_START_DELAY,
    DEFAULT_STOP_DELAY,
    DEFAULT_TARGET_GRID_POWER,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VOLTAGE,
)

_LOGGER = logging.getLogger(__name__)

UNAVAILABLE_STATES = ("unknown", "unavailable", None)


class PVSurplusChargingManager:
    """Verwaltet die periodische Regelung für einen konfigurierten Wallbox-Eintrag."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.enabled = True
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

        min_current = data.get(CONF_MIN_CURRENT, DEFAULT_MIN_CURRENT)
        max_current = data.get(CONF_MAX_CURRENT, DEFAULT_MAX_CURRENT)
        step = data.get(CONF_CURRENT_STEP, DEFAULT_CURRENT_STEP)
        voltage = data.get(CONF_VOLTAGE, DEFAULT_VOLTAGE)
        phases = data.get(CONF_PHASES, DEFAULT_PHASES)
        target = data.get(CONF_TARGET_GRID_POWER, DEFAULT_TARGET_GRID_POWER)
        interval = data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        start_delay = data.get(CONF_START_DELAY, DEFAULT_START_DELAY)
        stop_delay = data.get(CONF_STOP_DELAY, DEFAULT_STOP_DELAY)
        charging_value = data.get(CONF_CHARGING_STATE_VALUE, DEFAULT_CHARGING_STATE_VALUE)

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

        is_charging = bool(status_state and status_state.state == charging_value)

        if raw_new_current < min_current:
            self._below_min_seconds += interval
            self._above_min_seconds = 0
        else:
            self._above_min_seconds += interval
            self._below_min_seconds = 0

        # Nicht genug Überschuss -> irgendwann stoppen
        if raw_new_current < min_current:
            if is_charging and self._below_min_seconds >= stop_delay:
                _LOGGER.info(
                    "Zu wenig PV-Überschuss (Netz: %.0f W), stoppe Ladevorgang", grid_power
                )
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": data[CONF_STOP_BUTTON_ENTITY]},
                    blocking=True,
                )
                self._last_setpoint = None
            return

        # Genug Überschuss -> ggf. starten
        if not is_charging:
            if self._above_min_seconds >= start_delay:
                _LOGGER.info(
                    "Ausreichend PV-Überschuss (Netz: %.0f W), starte Ladevorgang bei %s A",
                    grid_power,
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
                "Setze Ladestrom auf %s A (Netz: %.0f W, Ziel: %s W)",
                new_current,
                grid_power,
                target,
            )
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": data[CONF_CHARGE_CURRENT_ENTITY], "value": new_current},
                blocking=True,
            )
            self._last_setpoint = new_current

"""Ziel-Ladestand für das aktuell gewählte Auto."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_TARGET_SOC, DOMAIN, signal_car_changed
from .controller import PVSurplusChargingManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    manager: PVSurplusChargingManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PVSurplusChargingTargetSoc(manager, entry)])


class PVSurplusChargingTargetSoc(NumberEntity, RestoreEntity):
    """Ziel-Ladestand (%) für das aktuell gewählte Auto.

    Wird beim Wechsel des aktiven Autos automatisch auf dessen konfigurierten
    Standardwert zurückgesetzt, kann danach aber jederzeit manuell angepasst werden.
    """

    _attr_has_entity_name = True
    _attr_name = "Ziel-Ladestand"
    _attr_icon = "mdi:battery-charging-80"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, manager: PVSurplusChargingManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_target_soc"
        self._attr_native_value = DEFAULT_TARGET_SOC
        self._unsub_signal = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "PV Surplus Charging",
            "model": "PV-Überschussladesteuerung",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in ("unknown", "unavailable"):
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                pass
        self._manager.target_soc = self._attr_native_value

        @callback
        def _handle_car_changed() -> None:
            self._attr_native_value = self._manager.target_soc
            self.async_write_ha_state()

        self._unsub_signal = async_dispatcher_connect(
            self.hass, signal_car_changed(self._entry.entry_id), _handle_car_changed
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_signal is not None:
            self._unsub_signal()

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self._manager.set_target_soc(value)
        self.async_write_ha_state()

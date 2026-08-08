"""Switch-Entity zum Aktivieren/Deaktivieren der PV-Überschussladung."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .controller import PVSurplusChargingManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    manager: PVSurplusChargingManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PVSurplusChargingSwitch(manager, entry)])


class PVSurplusChargingSwitch(SwitchEntity, RestoreEntity):
    """Schalter, der die automatische PV-Überschussladung ein-/ausschaltet."""

    _attr_has_entity_name = True
    _attr_name = "PV-Überschussladen aktiv"
    _attr_icon = "mdi:solar-power-variant"

    def __init__(self, manager: PVSurplusChargingManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        self._attr_is_on = True

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
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self._manager.enabled = self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self._manager.enabled = True
        self._manager.reset_counters()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self._manager.enabled = False
        self._manager.reset_counters()
        self.async_write_ha_state()

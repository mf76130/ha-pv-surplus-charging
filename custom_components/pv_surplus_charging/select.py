"""Auswahl des aktuell zu ladenden Autos."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_CAR_NAME, DOMAIN, NONE_CAR_OPTION
from .controller import PVSurplusChargingManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    manager: PVSurplusChargingManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PVSurplusChargingCarSelect(manager, entry)])


class PVSurplusChargingCarSelect(SelectEntity, RestoreEntity):
    """Wählt aus, welches Auto aktuell an der Wallbox lädt."""

    _attr_has_entity_name = True
    _attr_name = "Aktuelles Auto"
    _attr_icon = "mdi:car-electric"

    def __init__(self, manager: PVSurplusChargingManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active_car"
        self._attr_current_option = NONE_CAR_OPTION

    @property
    def options(self) -> list[str]:
        return [car[CONF_CAR_NAME] for car in self._manager.get_cars()] + [NONE_CAR_OPTION]

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
        if last_state is not None and last_state.state in self.options:
            self._attr_current_option = last_state.state
        else:
            self._attr_current_option = NONE_CAR_OPTION

        selected = (
            None if self._attr_current_option == NONE_CAR_OPTION else self._attr_current_option
        )
        self._manager.set_active_car(selected)

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        selected = None if option == NONE_CAR_OPTION else option
        self._manager.set_active_car(selected)
        self.async_write_ha_state()

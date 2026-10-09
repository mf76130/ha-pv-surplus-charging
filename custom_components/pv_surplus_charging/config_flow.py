"""Config Flow für PV Surplus Charging."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DOMAIN,
)


def _base_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Schema für die Wallbox-/Regelparameter (ohne Autos)."""
    return vol.Schema(
        {
            vol.Required(
                CONF_CHARGE_CURRENT_ENTITY,
                default=defaults.get(CONF_CHARGE_CURRENT_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="number", device_class="current")
            ),
            vol.Required(
                CONF_STATUS_ENTITY, default=defaults.get(CONF_STATUS_ENTITY)
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_START_BUTTON_ENTITY,
                default=defaults.get(CONF_START_BUTTON_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="button")),
            vol.Required(
                CONF_STOP_BUTTON_ENTITY,
                default=defaults.get(CONF_STOP_BUTTON_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="button")),
            vol.Required(
                CONF_GRID_POWER_ENTITY,
                default=defaults.get(CONF_GRID_POWER_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required(
                CONF_PV_POWER_ENTITY,
                default=defaults.get(CONF_PV_POWER_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required(
                CONF_CHARGING_STATE_VALUE,
                default=defaults.get(
                    CONF_CHARGING_STATE_VALUE, DEFAULT_CHARGING_STATE_VALUE
                ),
            ): str,
            vol.Required(
                CONF_NOT_CONNECTED_STATES,
                default=defaults.get(

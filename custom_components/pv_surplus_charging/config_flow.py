"""Config Flow für PV Surplus Charging."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DOMAIN,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_CHARGE_CURRENT_ENTITY,
                default=defaults.get(CONF_CHARGE_CURRENT_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
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
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_CHARGING_STATE_VALUE,
                default=defaults.get(
                    CONF_CHARGING_STATE_VALUE, DEFAULT_CHARGING_STATE_VALUE
                ),
            ): str,
            vol.Required(
                CONF_TARGET_GRID_POWER,
                default=defaults.get(CONF_TARGET_GRID_POWER, DEFAULT_TARGET_GRID_POWER),
            ): vol.Coerce(float),
            vol.Required(
                CONF_MIN_CURRENT,
                default=defaults.get(CONF_MIN_CURRENT, DEFAULT_MIN_CURRENT),
            ): vol.Coerce(int),
            vol.Required(
                CONF_MAX_CURRENT,
                default=defaults.get(CONF_MAX_CURRENT, DEFAULT_MAX_CURRENT),
            ): vol.Coerce(int),
            vol.Required(
                CONF_CURRENT_STEP,
                default=defaults.get(CONF_CURRENT_STEP, DEFAULT_CURRENT_STEP),
            ): vol.Coerce(int),
            vol.Required(
                CONF_VOLTAGE, default=defaults.get(CONF_VOLTAGE, DEFAULT_VOLTAGE)
            ): vol.Coerce(int),
            vol.Required(
                CONF_PHASES, default=defaults.get(CONF_PHASES, DEFAULT_PHASES)
            ): vol.In([1, 3]),
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): vol.Coerce(int),
            vol.Required(
                CONF_START_DELAY,
                default=defaults.get(CONF_START_DELAY, DEFAULT_START_DELAY),
            ): vol.Coerce(int),
            vol.Required(
                CONF_STOP_DELAY,
                default=defaults.get(CONF_STOP_DELAY, DEFAULT_STOP_DELAY),
            ): vol.Coerce(int),
        }
    )


class PVSurplusChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow für PV Surplus Charging."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CHARGE_CURRENT_ENTITY])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="PV-Überschussladen", data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=_schema({}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "PVSurplusChargingOptionsFlow":
        return PVSurplusChargingOptionsFlow(config_entry)


class PVSurplusChargingOptionsFlow(config_entries.OptionsFlow):
    """Optionen nachträglich anpassen."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(current))

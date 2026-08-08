"""Config Flow für PV Surplus Charging."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
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


def _car_schema(*, with_add_another: bool) -> vol.Schema:
    """Schema für die Eingabe eines einzelnen Autos."""
    fields = {
        vol.Required(CONF_CAR_NAME): str,
        vol.Required(CONF_CAR_SOC_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="battery")
        ),
        vol.Required(CONF_CAR_TARGET_SOC, default=DEFAULT_TARGET_SOC): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX
            )
        ),
    }
    if with_add_another:
        fields[vol.Required("add_another", default=False)] = selector.BooleanSelector()
    return vol.Schema(fields)


class PVSurplusChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow für PV Surplus Charging."""

    VERSION = 1

    def __init__(self) -> None:
        self._base_data: dict[str, Any] = {}
        self._cars: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CHARGE_CURRENT_ENTITY])
            self._abort_if_unique_id_configured()
            self._base_data = user_input
            return await self.async_step_car()

        return self.async_show_form(
            step_id="user", data_schema=_base_schema({}), errors=errors
        )

    async def async_step_car(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            add_another = user_input.pop("add_another", False)
            self._cars.append(user_input)
            if add_another:
                return self.async_show_form(
                    step_id="car", data_schema=_car_schema(with_add_another=True)
                )
            data = {**self._base_data, CONF_CARS: self._cars}
            return self.async_create_entry(title="PV-Überschussladen", data=data)

        return self.async_show_form(
            step_id="car", data_schema=_car_schema(with_add_another=True)
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "PVSurplusChargingOptionsFlow":
        return PVSurplusChargingOptionsFlow(config_entry)


class PVSurplusChargingOptionsFlow(config_entries.OptionsFlow):
    """Nachträgliches Anpassen von Regelparametern und Autos."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._cars: list[dict[str, Any]] | None = None

    def _current(self) -> dict[str, Any]:
        return {**self._config_entry.data, **self._config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["settings", "cars"]
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            new_options = {**self._config_entry.options, **user_input}
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="settings", data_schema=_base_schema(self._current())
        )

    async def async_step_cars(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if self._cars is None:
            self._cars = list(self._current().get(CONF_CARS, []))
        return self.async_show_menu(
            step_id="cars", menu_options=["add_car", "remove_car", "save_cars"]
        )

    async def async_step_add_car(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._cars.append(user_input)
            return await self.async_step_cars()

        return self.async_show_form(
            step_id="add_car", data_schema=_car_schema(with_add_another=False)
        )

    async def async_step_remove_car(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if not self._cars:
            return await self.async_step_cars()

        if user_input is not None:
            to_remove = set(user_input.get("remove", []))
            self._cars = [c for c in self._cars if c[CONF_CAR_NAME] not in to_remove]
            return await self.async_step_cars()

        names = [car[CONF_CAR_NAME] for car in self._cars]
        schema = vol.Schema(
            {
                vol.Optional("remove", default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=names, multiple=True)
                )
            }
        )
        return self.async_show_form(step_id="remove_car", data_schema=schema)

    async def async_step_save_cars(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        new_options = {**self._config_entry.options, CONF_CARS: self._cars}
        return self.async_create_entry(title="", data=new_options)

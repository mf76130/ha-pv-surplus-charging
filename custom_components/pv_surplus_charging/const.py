"""Konstanten für PV Surplus Charging."""

DOMAIN = "pv_surplus_charging"
PLATFORMS = ["switch"]

# Konfigurations-Keys (Entitäten)
CONF_CHARGE_CURRENT_ENTITY = "charge_current_entity"
CONF_STATUS_ENTITY = "status_entity"
CONF_START_BUTTON_ENTITY = "start_button_entity"
CONF_STOP_BUTTON_ENTITY = "stop_button_entity"
CONF_GRID_POWER_ENTITY = "grid_power_entity"

# Konfigurations-Keys (Regelparameter)
CONF_CHARGING_STATE_VALUE = "charging_state_value"
CONF_TARGET_GRID_POWER = "target_grid_power"
CONF_MIN_CURRENT = "min_current"
CONF_MAX_CURRENT = "max_current"
CONF_CURRENT_STEP = "current_step"
CONF_VOLTAGE = "voltage"
CONF_PHASES = "phases"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_START_DELAY = "start_delay"
CONF_STOP_DELAY = "stop_delay"

# Defaults
DEFAULT_TARGET_GRID_POWER = -100
DEFAULT_MIN_CURRENT = 6
DEFAULT_MAX_CURRENT = 16
DEFAULT_CURRENT_STEP = 1
DEFAULT_VOLTAGE = 230
DEFAULT_PHASES = 3
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_START_DELAY = 60
DEFAULT_STOP_DELAY = 60
DEFAULT_CHARGING_STATE_VALUE = "charging"

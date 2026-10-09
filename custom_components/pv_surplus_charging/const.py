"""Konstanten für PV Surplus Charging."""

DOMAIN = "pv_surplus_charging"
PLATFORMS = ["switch", "select", "number"]

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
CONF_NOT_CONNECTED_STATES = "not_connected_states"
CONF_PV_POWER_ENTITY = "pv_power_entity"

# Konfigurations-Keys (Autos)
CONF_CARS = "cars"
CONF_CAR_NAME = "name"
CONF_CAR_SOC_ENTITY = "soc_entity"
CONF_CAR_TARGET_SOC = "target_soc"
CONF_CAR_MIN_CURRENT = "min_current"

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
DEFAULT_TARGET_SOC = 80
DEFAULT_NOT_CONNECTED_STATES = "idle,sleep,fault"

# Sentinel-Option für "kein Auto ausgewählt"
NONE_CAR_OPTION = "Kein Auto ausgewählt"


def signal_car_changed(entry_id: str) -> str:
    """Dispatcher-Signal-Name, wenn sich das aktive Auto ändert."""
    return f"{DOMAIN}_{entry_id}_car_changed"

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging

from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNKNOWN,
    STATE_ON,
    ATTR_MODE,
    ATTR_STATE,
    ATTR_ICON,
    CONF_HOST
)
from homeassistant.components.fan import (
    FanEntity,
    SUPPORT_SET_SPEED,
    SUPPORT_PRESET_MODE,
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    ATTR_PERCENTAGE,
    ATTR_PERCENTAGE_STEP
)

from .const import (
    DOMAIN,
    FAN_DEVICES,
    STATES_MANAGER,
    MODE_AUTO,
    MODE_MANUALLY,
    MODE_TIMING,
    DEVICE_INFO,
    SPEED_OFF,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_HIGH,
    ATTR_SPEED
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_MODE = "set_mode"
ATTR_MODE_LIST = "mode_list"

SET_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_MODE): cv.string,
    }
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    states_manager = hass.data[config_entry.entry_id][STATES_MANAGER]
    hass.data[config_entry.entry_id][FAN_DEVICES] = []
    dev = FreshAirFan(states_manager, config_entry.data[CONF_HOST])
    hass.data[config_entry.entry_id][FAN_DEVICES].append(dev)

    async_add_entities(hass.data[config_entry.entry_id][FAN_DEVICES])


class FreshAirFan(FanEntity):
    def __init__(self, states_manager, host):
        self._unique_id = f"{DOMAIN}.{host}"
        self.entity_id = self._unique_id
        self._states_manager = states_manager
        self._state = STATE_UNKNOWN
        self._mode = MODE_AUTO
        self._speed = 0
        self._icon = "mdi:fan"
        self._device_info = DEVICE_INFO
        self._device_info["identifiers"] = {(DOMAIN, host)}
        self._attr_preset_modes = [MODE_AUTO, MODE_MANUALLY, MODE_TIMING]
        self._attr_supported_features = SUPPORT_SET_SPEED | SUPPORT_PRESET_MODE
        self._states_manager.set_fan_update(self.update_status)

    def set_percentage(self, percentage: int) -> None:

        if percentage == 0:
            speed = SPEED_OFF
        elif percentage <= 33:
            speed = SPEED_LOW
        elif percentage <= 66:
            speed = SPEED_MEDIUM
        else:
            speed = SPEED_HIGH
        self.set_speed(speed)

    async def async_set_percentage(self, percentage: int) -> None:
        await self.hass.async_add_executor_job(self.set_percentage, percentage)

    async def async_increase_speed(self):
        if self._speed != SPEED_HIGH:
            if self._speed == SPEED_OFF:
                speed = SPEED_LOW
            elif self._speed == SPEED_LOW:
                speed = SPEED_MEDIUM
            else:
                speed = SPEED_HIGH
            self.set_speed(speed)

    async def async_decrease_speed(self):
        if self._speed != SPEED_OFF:
            if self._speed == SPEED_HIGH:
                speed = SPEED_MEDIUM
            elif self._speed == SPEED_MEDIUM:
                speed = SPEED_LOW
            else:
                speed = SPEED_LOW
            self.set_speed(speed)

    def oscillate(self, oscillating: bool) -> None:
        pass

    def set_direction(self, direction: str) -> None:
        pass

    @property
    def speed_count(self) -> int:
        return 4

    @property
    def percentage_step(self) -> float:
        return 33

    @property
    def state(self):
        return self._state

    @property
    def is_on(self):
        return self._state == STATE_ON

    @property
    def percentage(self) -> int:
        if self._speed == SPEED_OFF:
            _percentage = 0
        elif self._speed == SPEED_LOW:
            _percentage = 33
        elif self._speed == SPEED_MEDIUM:
            _percentage = 66
        else:
            _percentage = 100
        return _percentage

    @property
    def device_info(self):
        return self._device_info

    @property
    def name(self):
        return "Air Handling Unit"

    @property
    def icon(self):
        return self._icon

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def preset_mode(self):
        return self._mode

    @property
    def capability_attributes(self):
        attrs = {}
        attrs[ATTR_PRESET_MODES] = self.preset_modes

        return attrs

    @property
    def state_attributes(self) -> dict:
        """Return optional state attributes."""
        data: dict[str, float | str | None] = {}
        data[ATTR_PERCENTAGE] = self.percentage
        data[ATTR_PERCENTAGE_STEP] = self.percentage_step
        data[ATTR_PRESET_MODE] = self.preset_mode
        return data

    @property
    def should_poll(self):
        return False

    def update_status(self, data: dict):
        if ATTR_SPEED in data:
            self._speed = data[ATTR_SPEED]
        if ATTR_MODE in data:
            self._mode = data[ATTR_MODE]
        if ATTR_STATE in data:
            self._state = data[ATTR_STATE]
        if ATTR_ICON in data:
            self._icon = data[ATTR_ICON]
        self.schedule_update_ha_state()

    def turn_on(
            self,
            percentage: int,
            preset_mode: str,
            **kwargs,
    ):
        self._states_manager.turn_on()

    def turn_off(self, **kwargs):
        self._states_manager.turn_off()

    def set_speed(self, speed: str):
        if speed != self._speed:
            self._states_manager.set_speed(speed)

    def set_preset_mode(self, preset_mode: str):
        if preset_mode != self._mode:
            self._states_manager.set_mode(preset_mode)
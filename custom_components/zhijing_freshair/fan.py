import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging

from typing import Optional
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNKNOWN,
    STATE_ON,
    STATE_OFF,
    ATTR_MODE,
    ATTR_STATE,
    ATTR_ICON,
    CONF_HOST
)
from homeassistant.components.fan import (
    FanEntity,
    ATTR_SPEED,
    SPEED_OFF,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_HIGH,
    SUPPORT_SET_SPEED,
    SERVICE_SET_SPEED,
    ATTR_SPEED_LIST
)

from .const import (
    DOMAIN,
    FAN_DEVICES,
    STATES_MANAGER,
    MODE_AUTO,
    MODE_MANUALLY,
    MODE_TIMING
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

    def service_handle(service):
        entity_id = service.data[ATTR_ENTITY_ID]
        fan_device = next(
            (fan for fan in hass.data[config_entry.entry_id][FAN_DEVICES] if fan.entity_id == entity_id),
            None,
        )

        if fan_device is None:
            return

        if service.service == SERVICE_SET_MODE:
            fan_device.set_mode(service.data[ATTR_MODE])

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MODE,
        service_handle,
        schema=SET_MODE_SCHEMA,
    )


class FreshAirFan(FanEntity):
    def __init__(self, states_manager, host):
        self._unique_id = f"{DOMAIN}.{host}"
        self.entity_id = self._unique_id
        self._states_manager = states_manager
        self._state = STATE_UNKNOWN
        self._mode = MODE_AUTO
        self._speed = SPEED_OFF
        self._icon = "mdi:fan"
        self._device_info = {
            "manufacturer": "BLAUBERG",
            "model": "Komfort ERV D 150P V3",
            "name": "George's Air Handling Unit",
            "identifiers": {(DOMAIN, host)}
        }
        self._states_manager.set_fan_update(self.update)

    @property
    def state(self):
        return self._state

    @property
    def is_on(self):
        return self._state == STATE_ON

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
    def supported_features(self):
        return SUPPORT_SET_SPEED

    @property
    def mode(self):
        return self._mode

    @property
    def mode_list(self):
        return [MODE_AUTO, MODE_MANUALLY, MODE_TIMING]

    @property
    def speed(self):
        return self._speed

    @property
    def speed_list(self):
        return [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    @property
    def device_state_attributes(self) -> dict:
        return {
            ATTR_MODE: self.mode,
            ATTR_MODE_LIST: self.mode_list,
        }

    @property
    def should_poll(self):
        return False

    def update(self, data: dict):
        if ATTR_SPEED in data:
            self._speed = data[ATTR_SPEED]
        if ATTR_MODE in data:
            self._mode = data[ATTR_MODE]
        if ATTR_STATE in data:
            self._state = data[ATTR_STATE]
        if ATTR_ICON in data:
            self._icon = data[ATTR_ICON]
        self.schedule_update_ha_state()

    def set_mode(self, mode: str):
        self._states_manager.set_mode(mode)

    async def async_set_speed(self, speed: str):
        await self.hass.async_add_executor_job(self.set_speed, speed)

    def set_speed(self, speed: str):
        self._states_manager.set_speed(speed)

    def turn_on(self, speed: str, **kwargs) -> None:
        self._states_manager.turn_on()

    def turn_off(self, **kwargs) -> None:
        self._states_manager.turn_off()

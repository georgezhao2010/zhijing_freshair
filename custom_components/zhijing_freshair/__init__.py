import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.core import HomeAssistant
from .const import(
    DOMAIN,
    DEVICES,
    STATES_MANAGER
)

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    ATTR_ENTITY_ID,
)

from .statemanager import StateManager

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, hass_config: dict):
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.setLevel(logging.DEBUG)
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry):
    config = config_entry.data
    host = config[CONF_HOST]
    port = config[CONF_PORT]

    state_manager = StateManager(host, port)
    hass.data[DOMAIN][DEVICES] = []
    hass.data[DOMAIN][DEVICES].append(host)
    hass.data[config_entry.entry_id] = {}
    hass.data[config_entry.entry_id][STATES_MANAGER] = state_manager
    state_manager.open()

    for paltform in {"fan", "sensor"}:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(
            config_entry, paltform))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry):

    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")

    state_manager = hass.data[config_entry.entry_id][STATES_MANAGER]
    state_manager.close()
    hass.data[DOMAIN].pop(config_entry.data[CONF_HOST])
    if len(hass.data[DOMAIN]) == 0:
        hass.data.pop(DOMAIN)
    hass.data.pop(config_entry.entry_id)

    return True

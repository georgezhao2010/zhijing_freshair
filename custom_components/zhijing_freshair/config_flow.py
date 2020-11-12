import logging

from homeassistant import config_entries
import voluptuous as vol

from .const import (
    DOMAIN,
    DEVICES,
    DEFAULT_PORT
)

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None, error=None):
        if user_input is not None:
            if DOMAIN in self.hass.data and DEVICES in self.hass.data[DOMAIN] and \
                    user_input[CONF_HOST] in self.hass.data[DOMAIN][DEVICES]:
                return await self.async_step_user(error="device_exist")
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int)
            }),
            errors={"base": error} if error else None
        )

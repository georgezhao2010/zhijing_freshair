import logging

from homeassistant.helpers.entity import Entity

from .const import (
    DOMAIN,
    DEVICE_CLASS_PM25,
    DEVICE_CLASS_VOC,
    DEVICE_CLASS_FILTER,
    STATES_MANAGER,
    DEVICE_INFO
)

from homeassistant.const import (
    STATE_UNKNOWN,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    CONF_HOST
)

from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS
)

_LOGGER = logging.getLogger(__name__)

UNITS = {
    DEVICE_CLASS_TEMPERATURE: TEMP_CELSIUS,
    DEVICE_CLASS_HUMIDITY: PERCENTAGE,
    DEVICE_CLASS_PM25: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER ,
    DEVICE_CLASS_VOC: CONCENTRATION_PARTS_PER_MILLION ,
    DEVICE_CLASS_FILTER: PERCENTAGE,
}

NAMES = {
    DEVICE_CLASS_TEMPERATURE: "Air Handling Unit Temperature",
    DEVICE_CLASS_HUMIDITY: "Air Handling Unit Humidity",
    DEVICE_CLASS_PM25: "Air Handling Unit PM2.5",
    DEVICE_CLASS_VOC: "Air Handling Unit VOC",
    DEVICE_CLASS_FILTER: "Air Handling Unit Filter"
}

ICONS = {
    DEVICE_CLASS_PM25: "mdi:air-humidifier",
    DEVICE_CLASS_VOC: "mdi:air-humidifier",
    DEVICE_CLASS_FILTER: "mdi:air-filter",
}

SENSOR_TYPES = [
    DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_PM25, DEVICE_CLASS_VOC, DEVICE_CLASS_FILTER
]

async def async_setup_entry(hass, config_entry, async_add_entities):
    sensors = []
    states_manager = hass.data[config_entry.entry_id][STATES_MANAGER]
    for sensor_type in SENSOR_TYPES:
        sensor = FreshairSensor(states_manager, sensor_type, config_entry.data[CONF_HOST])
        sensors.append(sensor)

    async_add_entities(sensors)

class FreshairSensor(Entity):
    def __init__(self, states_manager, sensor_type, host):
        self._state = STATE_UNKNOWN
        self._unique_id = "sensor.{}_{}".format(host, sensor_type)
        self.entity_id = self._unique_id
        self._sensor_type = sensor_type
        self._device_info = DEVICE_INFO
        self._device_info["identifiers"] = {(DOMAIN, host)}

        states_manager.add_sensor_update(sensor_type, self.update)

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        return self._device_info

    @property
    def should_poll(self):
        return False

    @property
    def device_class(self):
        return self._sensor_type

    @property
    def name(self):
        return NAMES.get(self._sensor_type)

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def unit_of_measurement(self):
        return UNITS.get(self._sensor_type)

    @property
    def icon(self):
        return ICONS.get(self._sensor_type)

    def update(self, state):
        self._state = state
        self.schedule_update_ha_state()
from datetime import timedelta
import logging
import random

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import event
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .api import get_balance

LOGGER = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([EdenredSensor(**data)])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])


class EdenredSensor(RestoreEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "kc"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_should_poll = False

    def __init__(self, name, card_number, pan):
        self._attr_name = name
        self.card_number = card_number
        self.pan = pan

    @property
    def unique_id(self):
        return self.card_number

    async def async_added_to_hass(self):
        last_state = await self.async_get_last_state()
        if last_state and last_state.state != STATE_UNKNOWN:
            self._attr_native_value = last_state.state
            self.schedule_fetch()
        else:
            await self.fetch()

    async def async_will_remove_from_hass(self):
        if self.cancel:
            self.cancel()

    def schedule_fetch(self):
        delay = timedelta(seconds=random.randint(12 * 60 * 60, 36 * 60 * 60))
        LOGGER.debug("Scheduling fetch for entity %s in %s", self.name, delay)
        self.cancel = event.async_call_later(self.hass, delay, self.fetch)

    async def fetch(self, x=None):
        LOGGER.debug("Fetching card for entity %s", self.name)
        self._attr_native_value = await get_balance(
            async_get_clientsession(self.hass), self.card_number, self.pan
        )
        self.async_write_ha_state()
        self.schedule_fetch()

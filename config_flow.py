import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN
from .api import EdenredException, get_balance


class EdenredConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, info):
        errors = {}

        if info:
            try:
                await get_balance(
                    async_get_clientsession(self.hass), info["card_number"], info["pan"]
                )

                info.setdefault("name", f'Edenred {info["card_number"]}')
                return self.async_create_entry(title=info["name"], data=info)
            except EdenredException as e:
                errors["base"] = str(e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("name"): str,
                    vol.Required("card_number"): str,
                    vol.Required("pan"): str,
                }
            ),
            errors=errors,
        )

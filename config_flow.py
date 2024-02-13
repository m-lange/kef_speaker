"""Config flow for KEF LSX II integration."""

from __future__ import annotations

import logging
from typing import Any
from .kef_connector import KefConnector

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.core import HomeAssistant
import homeassistant.helpers.aiohttp_client as hass_aiohttp
from homeassistant.data_entry_flow import FlowResult

from .exceptions import (
    CannotConnect
)

from .const import (
    DOMAIN, 
    CONF_HOST
)


_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect. """

    _LOGGER.debug("validate_input")

    try:

        host = data[CONF_HOST]
        session = hass_aiohttp.async_get_clientsession(hass)

        speaker = KefConnector(host, session, hass)

        _LOGGER.info(f"Trying to connect to KEF LSX II at {host}")
        mac_address = await speaker.mac_address
        device_name = await speaker.device_name

        if mac_address is None:
            raise CannotConnect()

    except Exception as e:
        _LOGGER.error(str(e))
        raise CannotConnect

    return {
        "title": device_name,
        CONF_HOST: data[CONF_HOST]
    }


class KefConfigFlow(ConfigFlow, domain = DOMAIN):
    """Handle a config flow for Dyson Pure Cool."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by user."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"


        data = {
            vol.Optional(CONF_HOST): str
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data),
            errors=errors,
        )
    

    async def async_step_import(self, user_input: dict) -> FlowResult:
        """Handle a flow initialized by import from configuration file."""

        info = await validate_input(self.hass, user_input)

        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured(updates={
            CONF_HOST: user_input[CONF_HOST]
        })

        return self.async_create_entry(title=info["title"], data=user_input)
    
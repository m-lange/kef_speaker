"""KEF LSX II integration."""

from __future__ import annotations

import logging
from .kef_connector import KefConnector

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.aiohttp_client as hass_aiohttp
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry


from .exceptions import CannotConnect

from .const import (
    DOMAIN, 
    CONF_HOST
)

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Optional(CONF_HOST, default=""): cv.string
        })
    },
    extra = vol.ALLOW_EXTRA
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up KEF LSX II from configuration file"""

    if DOMAIN not in config:
        return True
        
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN]
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KEF LSX II from a config entry."""

    try:
        host = entry.data[CONF_HOST]
        session = hass_aiohttp.async_get_clientsession(hass)

        speaker = KefConnector(host, session, hass)

        _LOGGER.info(f"Trying to connect to KEF LSX II at {host}")
        mac_address = await speaker.mac_address
        device_name = await speaker.device_name

        if mac_address is None:
            raise CannotConnect()

        # Store an instance of the "connecting" class that does the work of speaking
        # with your actual devices.
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = speaker

        for component in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, component)
            )

    except CannotConnect:
        _LOGGER.error("Connection refused")
        raise ConfigEntryNotReady

    return True
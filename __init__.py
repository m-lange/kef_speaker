"""KEF LSX II integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
import homeassistant.helpers.aiohttp_client as hass_aiohttp
from homeassistant.helpers.typing import ConfigType

from .const import CONF_HOST, DOMAIN
from .exceptions import CannotConnect
from .kef_connector import KefConnector

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
    """Set up KEF LSX II from configuration file."""

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

        _LOGGER.info("Trying to connect to KEF LSX II at %s", host)
        mac_address = await speaker.mac_address

        if mac_address is None:
            _LOGGER.error("Connection refused")
            raise ConfigEntryNotReady from None

        # Store an instance of the "connecting" class that does the work of speaking
        # with your actual devices.
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = speaker
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    except CannotConnect:
        _LOGGER.error("Connection refused")
        raise ConfigEntryNotReady from None

    return True

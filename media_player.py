"""Provides functionality to interact KEF LSX II speakers."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .kef_connector import KefConnector

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up KEF LSX II fan from a config entry."""

    speaker = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities( [KefMediaPlayerEntity(hass, speaker)], update_before_add=True )


class KefMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a KEF LSX II media player entity."""

    def __init__(self, hass: HomeAssistant, speaker: KefConnector):
        self._speaker = speaker
        self._name = None
        self._attr_icon = "mdi:speaker-wireless"


    @property
    def should_poll(self):
        """Push an update after each command."""
        return False


    @property
    def name(self) -> str:
        return self._name


    async def async_update(self):

        if self.name is None:
            self._name = await self._speaker.device_name
        if self.unique_id is None:
            self._attr_unique_id = "KEF_" + await self._speaker.mac_address

        self._attr_device_class = MediaPlayerDeviceClass.SPEAKER

        self._attr_device_info = {
            "identifiers": {(DOMAIN, await self._speaker.mac_address)},
            "name": await self._speaker.device_name,
            "manufacturer": "KEF",
            "model": await self._speaker.model,
            "configuration_url": "http://" + await self._speaker.ip_address,
            "sw_version": await self._speaker.firmware_version
        }

        controls = await self._speaker.controls

        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

        if controls["pause"]:    self._attr_supported_features |= MediaPlayerEntityFeature.PAUSE
        if controls["next"]:     self._attr_supported_features |= MediaPlayerEntityFeature.NEXT_TRACK
        if controls["previous"]: self._attr_supported_features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if controls["seekTime"]: self._attr_supported_features |= MediaPlayerEntityFeature.SEEK
        if controls["repeat"]:   self._attr_supported_features |= MediaPlayerEntityFeature.REPEAT_SET
        if controls["shuffle"]:  self._attr_supported_features |= MediaPlayerEntityFeature.SHUFFLE_SET

        poll_speaker = await self._speaker.poll_speaker()

        self._attr_source = await self._speaker.source
        self._attr_source_list = [ "wifi", "bluetooth", "tv", "optical", "usb", "analog" ]
        self._attr_sound_mode = None
        self._attr_sound_mode_list = None

        self._attr_volume_level = await self._speaker.volume_level / 100
        self._attr_volume_step = await self._speaker.volume_step / 100
        self._attr_volume_max = await self._speaker.maximum_volume / 100
        self._attr_is_volume_muted = await self._speaker.is_volume_muted

        if await self._speaker.source == "standby":
            self._attr_state = MediaPlayerState.OFF
        if await self._speaker.source == "powerOn":
            self._attr_state = MediaPlayerState.STANDBY
        elif await self._speaker.source in [ "wifi", "bluetooth", "tv", "optical", "usb", "analog" ]:
            self._attr_state = MediaPlayerState.ON
        elif await self._speaker.state == "playing":
            self._attr_state = MediaPlayerState.PLAYING
        elif await self._speaker.state == "paused":
            self._attr_state = MediaPlayerState.PAUSED
        elif await self._speaker.state == "stopped":
            self._attr_state = MediaPlayerState.IDLE
        else:
            self._attr_state = MediaPlayerState.STANDBY


        self._attr_app_id = poll_speaker["app_id"]
        self._attr_app_name = poll_speaker["app_name"]
        self._attr_media_content_id = poll_speaker["media_content_id"]
        self._attr_media_content_type = poll_speaker["media_content_type"]
        self._attr_group_members = None

        self._attr_media_position_updated_at = dt_util.utcnow()
        if poll_speaker["media_position"] is not None:
            self._attr_media_position = poll_speaker["media_position"] / 1000
        if poll_speaker["media_duration"] is not None:
            self._attr_media_position = poll_speaker["media_duration"] / 1000

        self._attr_media_image_url = poll_speaker["media_image_url"]
        self._attr_media_title = poll_speaker["media_title"] 
        self._attr_media_artist = poll_speaker["media_artist"]
        self._attr_media_album_name = poll_speaker["media_album_name"] 
        self._attr_media_album_artist = poll_speaker["media_album_artist"] 
        self._attr_media_playlist = poll_speaker["media_playlist"]
        self._attr_media_channel = poll_speaker["media_channel"]
        self._attr_media_episode = poll_speaker["media_episode"]
        self._attr_media_season = poll_speaker["media_season"]
        self._attr_media_track = poll_speaker["media_track"] 
        self._attr_media_series_title = poll_speaker["media_series_title"]

        self.async_schedule_update_ha_state(True)


    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self._speaker.turn_on()

        await asyncio.sleep(5)
        self.async_schedule_update_ha_state(True)


    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self._speaker.turn_off()

        await asyncio.sleep(5)
        self.async_schedule_update_ha_state(True)


    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if mute: await self._speaker.mute()
        else:    await self._speaker.unmute()


    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        volume = int( min(volume, self._attr_volume_max) * 100)
        await self._speaker.set_volume(volume)


    async def async_volume_up(self) -> None:
        """Turn volume up for media player."""
        volume = int( min(self._attr_volume_level + self._attr_volume_step, self._attr_volume_max) * 100)
        await self._speaker.set_volume(volume)


    async def async_volume_down(self) -> None:
        """Turn volume down for media player."""
        volume = int( min(self._attr_volume_level - self._attr_volume_step, self._attr_volume_max) * 100)
        await self._speaker.set_volume(volume)


    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        await self._speaker.set_source(source)

        await asyncio.sleep(0.25)
        self.async_schedule_update_ha_state(True)


    async def async_media_play_pause(self) -> None:
        """Play or pause the media player."""
        await self._speaker.play_pause()

        await asyncio.sleep(0.25)
        self.async_schedule_update_ha_state(True)


    async def async_media_play(self) -> None:
        """Send play command."""
        await self._speaker.play_pause()

        await asyncio.sleep(0.25)
        self.async_schedule_update_ha_state(True)


    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self._speaker.play_pause()

        await asyncio.sleep(0.25)
        self.async_schedule_update_ha_state(True)


    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self._speaker.next_track()

        await asyncio.sleep(0.25)
        self.async_schedule_update_ha_state(True)


    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self._speaker.previous_track()

        await asyncio.sleep(0.25)
        self.async_schedule_update_ha_state(True)

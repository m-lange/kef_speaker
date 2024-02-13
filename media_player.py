"""Provides functionality to interact KEF LSX II speakers."""

from __future__ import annotations
import asyncio

import logging
from homeassistant.components.media_player.const import MediaPlayerEntityFeature, MediaPlayerState, MediaType, RepeatMode

import homeassistant.util.dt as hass_dt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .kef_connector import KefConnector
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    BrowseMedia
)

from .const import (
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up KEF LSX II fan from a config entry"""

    speaker = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities( [KefMediaPlayerEntity(speaker)], update_before_add=True )


class KefMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a KEF LSX II media player entity."""

    def __init__(self, speaker: KefConnector):
        self._speaker = speaker
        self._name = None
        self._attr_icon = "mdi:speaker-wireless"


    @property
    def should_poll(self):
        """Push an update after each command."""
        return True
    

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

        # MediaPlayerEntityFeature.BROWSE_MEDIA
        # MediaPlayerEntityFeature.PLAY_MEDIA
            

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
            self._attr_state = MediaPlayerState.OFF # MediaPlayerState.STANDBY
        elif await self._speaker.source in [ "powerOn", "tv", "optical", "analog" ]:
            self._attr_state = MediaPlayerState.ON
        elif await self._speaker.state == "playing":
            self._attr_state = MediaPlayerState.PLAYING
        elif await self._speaker.state == "paused":
            self._attr_state = MediaPlayerState.PAUSED
        elif await self._speaker.state == "stopped":
            self._attr_state = MediaPlayerState.IDLE
        else:
            self._attr_state = MediaPlayerState.STANDBY


        if await self._speaker.play_mode in [ "repeatAll", "shuffleRepeatAll" ]:
            self._attr_repeat = RepeatMode.ALL
        elif await self._speaker.play_mode in [ "repeatOne", "shuffleRepeatOne" ]:
            self._attr_repeat = RepeatMode.ONE
        else:
            self._attr_repeat = RepeatMode.OFF

        if await self._speaker.play_mode in [ "shuffleRepeatAll", "shuffleRepeatOne" ]:
            self._attr_shuffle = True
        else:
            self._attr_shuffle = False


        self._attr_app_id = poll_speaker["app_id"]
        self._attr_app_name = poll_speaker["app_name"]
        self._attr_media_content_id = poll_speaker["media_content_id"] 
        self._attr_media_content_type = poll_speaker["media_content_type"]
        self._attr_group_members = None

        self._attr_media_position_updated_at = hass_dt.utcnow()
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


    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper.

        Browses all available media_sources by default. Filters content_type
        based on the DMR's sink_protocol_info.
        """
        _LOGGER.debug(
            "async_browse_media(%s, %s)", media_content_type, media_content_id
        )

        # media_content_type is ignored; it's the content_type of the current
        # media_content_id, not the desired content_type of whomever is calling.

        if self.browse_unfiltered:
            content_filter = None
        else:
            content_filter = self._get_content_filter()

        return await media_source.async_browse_media(
            self.hass, media_content_id, content_filter=content_filter
        )


    def _get_content_filter(self) -> Callable[[BrowseMedia], bool]:
        """Return a function that filters media based on what the renderer can play.

        The filtering is pretty loose; it's better to show something that can't
        be played than hide something that can.
        """
        if not self._device or not self._device.sink_protocol_info:
            # Nothing is specified by the renderer, so show everything
            _LOGGER.debug("Get content filter with no device or sink protocol info")
            return lambda _: True

        _LOGGER.debug("Get content filter for %s", self._device.sink_protocol_info)
        if self._device.sink_protocol_info[0] == "*":
            # Renderer claims it can handle everything, so show everything
            return lambda _: True

        # Convert list of things like "http-get:*:audio/mpeg;codecs=mp3:*"
        # to just "audio/mpeg"
        content_types = set[str]()
        for protocol_info in self._device.sink_protocol_info:
            protocol, _, content_format, _ = protocol_info.split(":", 3)
            # Transform content_format for better generic matching
            content_format = content_format.lower().replace("/x-", "/", 1)
            content_format = content_format.partition(";")[0]

            if protocol in STREAMABLE_PROTOCOLS:
                content_types.add(content_format)

        def _content_filter(item: BrowseMedia) -> bool:
            """Filter media items by their media_content_type."""
            content_type = item.media_content_type
            content_type = content_type.lower().replace("/x-", "/", 1).partition(";")[0]
            return content_type in content_types

        return _content_filter

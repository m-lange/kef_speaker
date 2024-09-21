"""Class to control KEF LS50 Wireless II, LSX II and LS60."""

import homeassistant.helpers.aiohttp_client as hass_aiohttp


class KefConnector:
    """Connector class to control KEF LS50 Wireless II, LSX II and LS60."""

    def __init__(self, host, session=None, hass=None):
        """Initialize connector class."""
        self._host = host
        self._session = session
        self._hass = hass
        self._previous_source = "wifi"
        self._getDataUrl = "http://" + self._host + "/api/getData"
        self._setDataUrl = "http://" + self._host + "/api/setData"


    async def close_session(self) -> None:
        """Close session."""
        if self._session is not None:
            await self._session.close()
            self._session = None


    async def resurect_session(self) -> None:
        """Resurect session."""
        if self._session is None:
            self._session = hass_aiohttp.async_get_clientsession(self._hass)



    @property
    async def mac_address(self) -> str | None:
        """Get the mac address of the Speaker."""
        response = await self._get("settings:/system/primaryMacAddress")
        return response[0].get("string_", None)


    @property
    async def ip_address(self) -> str:
        """Get the ip address of the Speaker."""
        return self._host


    @property
    async def device_name(self) -> str | None:
        """Get the friendly name of the Speaker."""
        response = await self._get("settings:/deviceName")
        return response[0].get("string_", None)


    @property
    async def model(self) -> str | None:
        """Get the model of the speaker."""
        response = await self._get("settings:/releasetext")
        return response[0].get("string_", "?_?").split("_")[0]


    @property
    async def firmware_version(self) -> str:
        """Get the firmware version of the speaker."""
        response = await self._get("settings:/releasetext")
        return response[0].get("string_", "?_?").split("_")[1]


    @property
    async def state(self) -> str | None:
        """State of the speaker : 'playing', 'paused', 'stopped'."""
        response = await self._get("player:player/data")
        return response[0].get("state", None)


    @property
    async def controls(self) -> dict:
        """Possible control functions of the speaker."""

        response = await self._get("player:player/data")

        controls = {}
        controls["previous"]  = response[0].get("controls", {}).get("previous", False)
        controls["pause"]     = response[0].get("controls", {}).get("pause", False)
        controls["next"]      = response[0].get("controls", {}).get("next_", False)
        controls["seekTrack"] = response[0].get("controls", {}).get("seekTrack", False)
        controls["seekTime"]  = response[0].get("controls", {}).get("seekTime", False)
        controls["seekBytes"] = response[0].get("controls", {}).get("seekBytes", False)
        controls["like"]      = response[0].get("controls", {}).get("like", False)
        controls["dislike"]   = response[0].get("controls", {}).get("dislike", False)

        controls["playMode"]                     = {}
        controls["playMode"]["repeatAll"]        = response[0].get("controls", {}).get("playMode", {}).get("repeatAll", False)
        controls["playMode"]["shuffleRepeatAll"] = response[0].get("controls", {}).get("playMode", {}).get("shuffleRepeatAll", False)
        controls["playMode"]["shuffle"]          = response[0].get("controls", {}).get("playMode", {}).get("shuffle", False)
        controls["playMode"]["repeatOne"]        = response[0].get("controls", {}).get("playMode", {}).get("repeatOne", False)
        controls["playMode"]["shuffleRepeatOne"] = response[0].get("controls", {}).get("playMode", {}).get("shuffleRepeatOne", False)

        controls["repeat"]  = controls["playMode"]["repeatAll"] or controls["playMode"]["repeatOne"]
        controls["shuffle"] = controls["playMode"]["shuffle"]

        return controls


    @property
    async def play_mode(self) -> str | None:
        """Play mode of the speaker."""
        response = await self._get("settings:/mediaPlayer/playMode")
        return response[0].get("playerPlayMode", None)


    @property
    async def status(self) -> str | None:
        """Status of the speaker : 'standby' or 'powerOn'."""
        response = await self._get("settings:/kef/host/speakerStatus")
        return response[0].get("kefSpeakerStatus", None)


    @property
    async def source(self) -> str | None:
        """Input source of the speaker : 'standby', 'powerOn', 'wifi', 'bluetooth', 'tv', 'optical', 'usb', 'analog'."""
        response = await self._get("settings:/kef/play/physicalSource")
        return response[0].get("kefPhysicalSource", None)


    @property
    async def volume_level(self) -> int | None:
        """Volume level of the speaker."""
        response = await self._get("player:volume")
        return response[0].get("i32_", None)


    @property
    async def volume_step(self) -> int | None:
        """Return the step to be used by the volume_up and volume_down services."""
        response = await self._get("settings:/kef/host/volumeStep")
        return response[0].get("i16_", None)


    @property
    async def is_volume_limited(self) -> int | None:
        """Boolean if volume is limited."""
        response = await self._get("settings:/kef/host/volumeLimit")
        return response[0].get("bool_", None)


    @property
    async def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        response = await self._get("settings:/mediaPlayer/mute")
        return response[0].get("bool_", None) == "True"


    @property
    async def maximum_volume(self) -> bool | None:
        """Maximum volume of the speaker."""
        response = await self._get("settings:/kef/host/maximumVolume")
        return response[0].get("i32_", None)


    async def set_status(self, status: str) -> None:
        """Set status of the speaker."""
        await self._set("settings:/kef/host/speakerStatus", "kefSpeakerStatus", status)


    async def set_source(self, source: str) -> None:
        """Set the input source of the speaker."""
        await self._set("settings:/kef/play/physicalSource", "kefPhysicalSource", source)


    async def turn_on(self) -> None:
        """Turn the speaker on."""
        await self.set_source(self._previous_source)


    async def turn_off(self) -> None:
        """Turn the speaker off."""
        self._previous_source = await self.source
        await self.set_source("standby")


    async def set_volume(self, volume: int) -> None:
        """Set volume level of the speaker."""
        await self._set("player:volume", "i32_", volume)


    async def mute(self) -> None:
        """Mute the volume of the speaker."""
        await self._set("settings:/mediaPlayer/mute", "bool_", "True")


    async def unmute(self) -> None:
        """Unmuute the volume of the speaker."""
        await self._set("settings:/mediaPlayer/mute", "bool_", "False")


    async def play_pause(self) -> None:
        """Send play command."""
        await self._control("pause")


    async def previous_track(self) -> None:
        """Send play command."""
        await self._control("previous")


    async def next_track(self) -> None:
        """Send play command."""
        await self._control("next")


    async def like(self) -> None:
        """Send play command."""
        await self._control("like")


    async def dislike(self) -> None:
        """Send play command."""
        await self._control("dislike")


    async def seek(self, position: int) -> None:
        """Send seek command."""
        await self._control("seekTime", "time", position)


    async def set_play_mode(self, play_mode: str) -> None:
        """Set play mode of the speaker."""
        await self._set("settings:/mediaPlayer/playMode", "playerPlayMode", play_mode)


    async def play_media(self, uri: str) -> None:
        """Send seek command."""
        await self._control("play", "media", uri)


    async def _get(self, path: str) -> list[dict]:
        payload = {
            "path": path,
            "roles": "value"
        }

        await self.resurect_session()
        async with self._session.get(self._getDataUrl, params=payload) as response:
            return await response.json()



    async def _set(self, path: str, type: str, value: str) -> None:
        payload = {
            "path": path,
            "roles": "value",
            "value": f"""{{"type":"{type}","{type}":"{value}"}}"""
        }

        await self.resurect_session()
        async with self._session.get(self._setDataUrl, params=payload) as response:
            await response.json()


    async def _control(self, command: str, type: str|None = None, value: str|None = None) -> None:

        payload = {
            "path": "player:player/control",
            "roles": "activate"
        }

        if type is None and value is None:
            payload["value"] = f"""{{"control":"{command}"}}"""
        else:
            payload["value"] = f"""{{"control":"{command}", "{type}": "{value}" }}"""

        await self.resurect_session()
        async with self._session.get(self._setDataUrl, params=payload) as response:
            await response.json()



    async def poll_speaker(self) -> dict:
        """Poll speaker for information."""

        poll_speaker = {}
        response = await self._get("player:player/data/playTime")

        # Position of current playing media.
        poll_speaker["media_position"] = response[0].get("i64_", None)


        response = await self._get("player:player/data")

        # Duration of current playing media.
        poll_speaker["media_duration"] = response[0].get("status", {}).get("duration", None)

        # Image url of current playing media.
        poll_speaker["media_image_url"] = response[0].get("trackRoles", {}).get("icon", None)

        # Title of current playing media.
        poll_speaker["media_title"] = response[0].get("trackRoles", {}).get("title", None)

        # Artist of current playing media, music track only.
        poll_speaker["media_artist"] = response[0].get("trackRoles", {}).get("mediaData", {}).get("metaData", {}).get("artist", None)

        # Album name of current playing media, music track only.
        poll_speaker["media_album_name"] = response[0].get("trackRoles", {}).get("mediaData", {}).get("metaData", {}) .get("album", None)


        # Title of Playlist currently playing.
        poll_speaker["media_playlist"] = response[0].get("mediaRoles", {}).get("title", None)

        # Content ID of current playing media.
        poll_speaker["media_content_id"] = response[0].get("trackRoles", {}).get("id", None)
        if poll_speaker["media_content_id"] is None:
            poll_speaker["media_content_id"] = response[0].get("mediaRoles", {}).get("id", None)

        # Content type of current playing media.
        poll_speaker["media_content_type"] = response[0].get("mediaRoles", {}).get("mediaData", {}).get("resources", [{}])[0].get("mimeType", None)
        if poll_speaker["media_content_type"] is None:
            poll_speaker["media_content_type"] = response[0].get("trackRoles", {}).get("mediaData", {}).get("resources", [{}])[0].get("mimeType", None)
        if poll_speaker["media_content_type"] is None:
            poll_speaker["media_content_type"] = response[0].get("mediaRoles", {}).get("type", None)
        if poll_speaker["media_content_type"] is None:
            poll_speaker["media_content_type"] = response[0].get("trackRoles", {}).get("type", None)

        # ID of the current running app.
        poll_speaker["app_id"] = response[0].get("trackRoles", {}).get("mediaData", {}).get("metaData", {}) .get("serviceID", None)
        if poll_speaker["app_id"] is None:
            poll_speaker["app_id"] = response[0].get("mediaRoles", {}).get("mediaData", {}).get("metaData", {}) .get("serviceID", None)

        # Name of the current running app.
        poll_speaker["app_name"] = poll_speaker["app_id"]


        # Album artist of current playing media, music track only.
        poll_speaker["media_album_artist"] = None

        # Track number of current playing media, music track only.
        poll_speaker["media_track"] = None

        # Title of series of current playing media, TV show only.
        poll_speaker["media_series_title"] = None

        # Season of current playing media, TV show only.
        poll_speaker["media_season"] = None

        # Episode of current playing media, TV show only.
        poll_speaker["media_episode"] = None

        # Channel currently playing.
        poll_speaker["media_channel"] = None

        return poll_speaker

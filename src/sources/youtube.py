from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional
from urllib.parse import parse_qs, urlparse

import discord
import yt_dlp

from src.config import config
from src.music.track import Track

if TYPE_CHECKING:
    from src.music.playlist import Playlist


@dataclass
class RadioNotAllowedError(Exception):
    message: str = 'You can\'t request YouTube Mixes. Sorry.'

    def __str__(self):
        return self.message


@dataclass
class NothingFoundError(Exception):
    message: str = 'Could not find anything on YouTube. Sorry.'

    def __str__(self):
        return self.message


@dataclass
class RestrictedVideoError(Exception):
    message: str = 'Detected private video(s), skipping. Sorry.'

    def __str__(self):
        return self.message


class Handler:
    class ExtractionParams:
        @staticmethod
        def download() -> dict:
            return {
                'format': 'bestaudio/best',
                'title': True,
            }

        @staticmethod
        def from_url() -> dict:
            return {
                'format': 'bestaudio/best',
                'extract_flat': True,
                'skip_download': True,
                'title': True,
            }

        @staticmethod
        def from_search():
            return {
                'format': 'bestaudio/best',
                'default_search': 'ytsearch',
                'skip_download': True,
                'title': True,
                'noplaylist': True,
            }

        @staticmethod
        def from_playlist(start_pos: int) -> dict:
            return {
                'format': 'bestaudio/best',
                'extract_flat': True,
                'playliststart': start_pos,
                'playlistend': start_pos + config.MAX_PLAYLIST_LEN + 1,
            }

    @classmethod
    def from_playlist(cls, request: str) -> List[dict]:
        data_list = []
        link_params = parse_qs(request)
        start_pos = link_params.get('index', 0)
        if start_pos:
            start_pos = int(start_pos[0])
        # Default link params start with 'watch',
        # which makes yt-dlp think that its not a playlist for some reason
        id_list = (
            link_params.get('list') or [val for key, val in link_params.items() if 'list' in key][0]
        )  # Scuffed fix for youtu.be
        playlist_request = f'https://www.youtube.com/playlist?list={id_list[0]}'
        with yt_dlp.YoutubeDL(cls.ExtractionParams.from_playlist(start_pos)) as ytdl:
            info = ytdl.extract_info(playlist_request, download=False)
        entries = info.get('entries')
        for entry in entries:
            data_list.append(entry)
        return data_list

    @classmethod
    def from_url(cls, request: str) -> dict:
        with yt_dlp.YoutubeDL(cls.ExtractionParams.from_url()) as ytdl:
            info = ytdl.extract_info(request, download=False)

        if info is None:
            raise NothingFoundError

        return info

    @classmethod
    def from_search(cls, request: str) -> dict:
        with yt_dlp.YoutubeDL(cls.ExtractionParams.from_search()) as ytdl:
            search_result = ytdl.extract_info(request, download=False)

        info_list = search_result['entries']

        if info_list is None:
            raise NothingFoundError

        return info_list[0]

    @classmethod
    def download(cls, url: str) -> Optional[dict]:
        with yt_dlp.YoutubeDL(cls.ExtractionParams.download()) as ytdl:
            try:
                info = ytdl.extract_info(url, download=False)
            except Exception as ex:
                raise  # TODO: Some shit happened (from yt_dlp.utils import ExtractorError?)

        return info


class Info:
    webpage_url: str = None
    uploader: str = None
    title: str = None
    duration: int = None
    thumbnail: str = None

    def __init__(self, data: dict):
        if thumbnails := data.get('thumbnails'):
            self.thumbnail = thumbnails[len(thumbnails) - 1]['url']
        self.webpage_url = data.get('webpage_url')
        self.uploader = data.get('uploader')
        self.title = data.get('title')
        self.duration = data.get('duration')


class Source:
    TAGS: tuple = ('www.youtube.com', 'youtu.be')
    __slots__ = ('info',)

    def __init__(self, data):
        self.info = Info(data)

    @classmethod
    def track_from_data(cls, data: dict) -> Optional[Track]:
        if not data.get('channel_id'):
            # Private video
            return None
        if data.get('duration', 0) > config.MAX_SONG_DURATION:
            # Too long
            return None
        return Track(url=data.get('url'), source=cls(data=data))

    @classmethod
    def handle(cls, request: str, playlist: Playlist, requested_by: discord.Member) -> None:
        parsed_request = urlparse(request)
        if 'start_radio' in parsed_request.query:
            raise RadioNotAllowedError
        if parsed_request.scheme:
            if parsed_request.path == '/playlist' or 'list=' in parsed_request.query:
                data_list = Handler.from_playlist(request)
                for data in data_list:
                    if track := cls.track_from_data(data):
                        track.requested_by = requested_by
                        playlist.add(track)
                return
            data = Handler.from_url(request)
        else:
            data = Handler.from_search(request)

        if track := cls.track_from_data(data):
            track.requested_by = requested_by
            track.loaded = True
            playlist.add(track)

    def download(cls, track: 'Track') -> 'Track':
        data = Handler.download(track.url)
        loaded_track = cls.track_from_data(data)
        track.url = loaded_track.url
        track.source = loaded_track.source
        track.loaded = True
        return track

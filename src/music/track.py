from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

import discord

if TYPE_CHECKING:
    from core.playlist import Playlist


class IInfo(Protocol):
    webpage_url: str = None
    uploader: str = None
    title: str = None
    duration: int = None
    thumbnail: str = None


class ISource(Protocol):
    info: IInfo

    @classmethod
    def handle(cls, request: str, playlist: 'Playlist', requested_by: discord.Member) -> None:
        ...

    @classmethod
    def download(cls, track: 'Track') -> 'Track':
        ...


@dataclass(kw_only=True, slots=True)
class Track:
    url: str
    source: ISource
    loaded: bool = False
    requested_by: discord.Member = field(init=False)

    def load(self) -> 'Track':
        return self.source.download(self)

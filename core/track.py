import datetime

import discord


class Track:
    __slots__ = ('url', 'requester', 'info')

    def __init__(self, url=None, requester=None, uploader=None, title=None, duration=None, webpage_url=None,
                 thumbnail=None):
        self.url = url
        self.requester = requester
        self.info = self.TrackInfo(uploader, title, duration, webpage_url, thumbnail)

    def __str__(self):
        return f'**`{self.info.title}`** requested by {self.requester.mention}'

    class TrackInfo:
        __slots__ = ('uploader', 'title', 'duration', 'webpage_url', 'thumbnail')

        def __init__(self, uploader=None, title=None, duration=None, webpage_url=None, thumbnail=None):
            self.uploader = uploader
            self.title = title
            self.duration = duration
            self.webpage_url = webpage_url
            self.thumbnail = thumbnail

    def create_embed(self):
        embed = discord.Embed(title='Now playing',
                              description=f'[{self.info.title}]({self.info.webpage_url})')
        duration_field_name = 'Song Duration'
        duration = str(datetime.timedelta(seconds=self.info.duration))
        embed.add_field(name=duration_field_name, value=duration)
        embed.add_field(name='Requested by', value=self.requester)
        embed.set_thumbnail(url=self.info.thumbnail)
        return embed

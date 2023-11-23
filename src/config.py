import os

GUILD_TO_MUSIC_PLAYER = {}


class Config:
    LOG_FORMAT = '%(levelname)-8s [%(asctime)s] %(name)s %(message)s'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARN')

    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_BOT_PREFIX = os.getenv('DISCORD_BOT_PREFIX')

    MAX_SONG_DURATION = 1.5 * 60 * 60  # Maximum song duration to play in seconds
    MAX_PLAYLIST_LEN = 50  # Maximum songs in playlist request to enqueue
    MAX_PRELOAD = 2  # Amount of songs to preload

    EMBED_QUEUE_PER_PAGE = 5  # Amount of enqueued songs to display in embed
    EMBED_HISTORY_PER_PAGE = 3  # Amount of recent songs to display in embed


config = Config

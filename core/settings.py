import json
from pathlib import Path

import discord

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    def __init__(self, guild):
        self.guild = guild
        self.json_data = None
        self.config = None
        self.path = f'{BASE_DIR}/config/generated/settings.json'

        self.settings_template = {
            "id": 0,
            "timeout": 5 * 60,
        }
        self.load()
        self.update()

    def load(self):
        data = open(self.path, 'r')
        self.json_data = json.load(data)
        for guild in self.json_data:
            guild_settings = self.json_data[guild]

            if guild_settings['id'] == self.guild.id:
                self.config = guild_settings

        if self.config is None:
            self.create()
            return

    def create(self):
        self.json_data[self.guild.id] = self.settings_template
        self.json_data[self.guild.id]['id'] = self.guild.id

        with open(self.path, 'w') as f:
            json.dump(self.json_data, f, indent=2)

        self.load()

    def update(self):
        upd_flag = False
        for key in self.settings_template.keys():
            if key not in self.config:
                self.config[key] = self.settings_template[key]
                upd_flag = True

        if upd_flag:
            with open(self.path, 'w') as f:
                json.dump(self.json_data, f)
            self.load()

    async def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title='Settings', description=self.guild.name)
        embed.set_thumbnail(url=self.guild.icon_url)
        for key, value in self.config.items():
            if key == 'id':
                continue
            if not value:
                value = ':x:'
            embed.add_field(name=key, value=value, inline=False)

        return embed

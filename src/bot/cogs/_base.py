import logging

from discord.ext import commands


class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('cogs')

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f'[ + ] {self.qualified_name}')

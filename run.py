import os

from dotenv import load_dotenv

import discord
from discord.ext import commands

from config import BOT_CMD_PREFIX
from general import setup

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or(BOT_CMD_PREFIX), intents=intents)
setup(bot)

if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORDBOT_TOKEN')
    bot.run(token, bot=True, reconnect=True)

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import BOT_CMD_PREFIX
from general import setup

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or(BOT_CMD_PREFIX), intents=intents)
setup(bot)

if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORDBOT_TOKEN')
    bot.run(token, reconnect=True)

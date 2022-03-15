import discord
from discord.ext import commands

from core.utils import get_similarity_coefficient


async def correct_command_name(bot: discord.client, ctx: commands.Context, command_name: str) -> str:
    tanimoto_max = 0
    names_and_aliases = []
    similar_command = None
    owner_id = bot.owner_id or (await bot.application_info()).owner.id
    if ctx.message.author.id == owner_id:
        cmd_list = bot.commands
    else:
        cmd_list = list(filter(lambda cmd: not cmd.hidden, bot.commands))
    for cmd in cmd_list:
        names_and_aliases.append(cmd.name)
        for alias in cmd.aliases:
            names_and_aliases.append(alias)
    for name in names_and_aliases:
        tanimoto_curr = get_similarity_coefficient(command_name, name)
        if tanimoto_curr > tanimoto_max:
            tanimoto_max = tanimoto_curr
            similar_command = name
    return similar_command

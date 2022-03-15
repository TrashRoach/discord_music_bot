import inspect

import discord
from discord.ext import commands

from config import CODE_BLOCK
from core.helpers import correct_command_name


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='source', aliases=['code'])
    async def _source(self, ctx: commands.Context, *, cmd: str = None):
        """Show source code for selected command."""
        symbol_limit = 2000 - 12  # code block open + Python + code block close
        if not cmd:
            cmd = 'source'
        cmd = cmd.lower()
        command = self.bot.get_command(cmd)
        if not command:
            await ctx.send('Can\'t find that command. Sorry.', delete_after=10)
            similar_command = await correct_command_name(self.bot, ctx, cmd)
            if similar_command:
                await ctx.send(f'Maybe you mean **`{similar_command}`** ?', delete_after=15)
            return
        source_code = inspect.getsource(command.callback)
        # Output
        while len(source_code) > symbol_limit:
            # Split by symbol_limit
            source_code_part = source_code[:symbol_limit]
            # Get first closest split index
            slice_index = source_code_part.rfind('\n')
            # Slice by index
            source_code_part = source_code_part[:slice_index]
            # Leftovers
            source_code = source_code[slice_index:]
            await ctx.send(f'{CODE_BLOCK}python\n{source_code_part}{CODE_BLOCK}')
        await ctx.send(f'{CODE_BLOCK}python\n{source_code}{CODE_BLOCK}')

    @commands.command(name='logout')
    @commands.is_owner()
    async def _logout(self, ctx: commands.Context):
        """Disconnect the bot.

        Owner only.
        """
        await ctx.send(f'Goodbye.')
        await self.bot.change_presence(status=discord.Status.invisible)
        await self.bot.close()

    @commands.command(name='owner', aliases=['owners', 'ownership'])
    async def _owner(self, ctx: commands.Context):
        """Tag Bot's owner(s)."""
        owner_id = self.bot.owner_id or (await self.bot.application_info()).owner.id
        composed_msg = f'Creator: <@{owner_id}>\n'
        owner_ids = self.bot.owner_ids
        if owner_ids:
            composed_msg += f'Owners: '
            for owner_id in owner_ids:
                composed_msg += f'<@{owner_id}>\n'
        await ctx.send(composed_msg)

    @commands.command(name='ping')
    async def _ping(self, ctx: commands.Context):
        """Pong."""
        await ctx.send('pong')

    # ToDo: settings
    # @commands.command(name='settings', aliases=['options'])
    # # @commands.is_owner()
    # async def _settings(self, ctx, *args):
    #     """Display the current guild settings."""
    #     sett = guild_to_settings[ctx.guild]
    #     if len(args) == 0:
    #         await ctx.send(embed=await sett.create_embed())
    #
    #     arg_list = list(args)


def setup(bot):
    bot.add_cog(Utility(bot))

from typing import Literal, Optional

import discord
from discord.ext import commands

from src.bot.cogs._base import BaseCog


class Management(BaseCog):
    """Commands controlling client's behaviour"""

    @commands.is_owner()
    @commands.hybrid_command()
    async def shutdown(self, ctx: commands.Context) -> None:
        """Logs the bot out."""

        await ctx.send('Logging out now...')
        await self.bot.close()

    @commands.guild_only()
    @commands.is_owner()
    @commands.command(name='sync')
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal['~', '*', '^']] = None,
    ) -> None:
        """Umbra's command for syncing CommandTree.

        sync
            This takes all global commands within the CommandTree and sends them to Discord.
        sync ~
            This will sync all guild commands for the current context’s guild.
        sync *
            This command copies all global commands to the current guild (within the CommandTree) and syncs.
        sync ^
            This command will remove all guild commands from the CommandTree and syncs,
            which effectively removes all commands from the guild.
        sync 123 456 789
            This command will sync the 3 guild ids we passed: 123, 456 and 789.
            Only their guilds and guild-bound commands.
        """

        if not guilds:
            if spec == '~':
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == '*':
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == '^':
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(f'Synced {len(synced)} commands {"globally" if spec is None else "to the current guild."}')
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f'Synced the tree to {ret}/{len(guilds)}.')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Management(bot))

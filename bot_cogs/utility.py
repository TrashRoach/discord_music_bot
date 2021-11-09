import discord
from discord.ext import commands


class Utility(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='off', aliases=['disconnect', 'logout', 'dc'])
    @commands.is_owner()
    async def off_(self, ctx):
        """Disconnect the bot."""
        await ctx.send(f'Goodbye.')
        await self.bot.change_presence(status=discord.Status.invisible)
        await self.bot.close()

    @commands.command(name='owner',aliases=['owners', 'ownership'])
    async def owner_(self, ctx):
        """Bot's owner(s), if any."""
        composed_msg = f'@<{self.bot.owner_id}>\n' if self.bot.owner_id else ''
        owner_ids = self.bot.owner_ids
        for owner_id in owner_ids:
            composed_msg += f'<@{owner_id}>\n'
        if not composed_msg:
            composed_msg = 'I have no master it seems.'
        await ctx.send(composed_msg)


def setup(bot):
    bot.add_cog(Utility(bot))

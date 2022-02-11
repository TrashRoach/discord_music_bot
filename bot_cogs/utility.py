import discord
from discord.ext import commands


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='off', aliases=['logout', 'dc'])
    @commands.is_owner()
    async def _off(self, ctx):
        """Disconnect the bot.

        Owner only.
        """
        await ctx.send(f'Goodbye.')
        await self.bot.change_presence(status=discord.Status.invisible)
        await self.bot.close()

    @commands.command(name='owner', aliases=['owners', 'ownership'])
    async def _owner(self, ctx):
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
    async def _ping(self, ctx):
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

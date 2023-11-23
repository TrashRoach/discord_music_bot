from discord.ext import commands

from src.bot.cogs._base import BaseCog


class Test(BaseCog, command_attrs=dict(hidden=True)):
    """
    Do you think God stays in heaven
    because he too lives in fear of what he's created?
    """

    @commands.is_owner()
    @commands.hybrid_command()
    async def test(self, ctx: commands.Context):
        await ctx.send('This is a hybrid command!')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Test(bot))

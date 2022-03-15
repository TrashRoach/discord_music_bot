import traceback

import discord
from discord.ext import commands

from core.helpers import correct_command_name


class Errors(commands.Cog):
    """Error handling"""

    __slots__ = ('bot',)

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.

        Parameters
        -----------
        ctx:    commands.Context
            The context used for command invocation.
        error:   commands.CommandError
            The Exception raised.
        """
        if isinstance(error, commands.MissingRequiredArgument):
            message = await ctx.send(f"{error.param.name.capitalize()} is a required argument that is missing.",
                                     delete_after=10)
        elif isinstance(error, commands.NotOwner):
            message = await ctx.send("You do not have the necessary permissions to execute this command.",
                                     delete_after=10)
        elif isinstance(error, commands.MissingPermissions):
            message = await ctx.send("You do not have the necessary permissions to execute this command.",
                                     delete_after=10)
        elif isinstance(error, commands.CheckFailure):
            message = await ctx.send("You cannot use this command.",
                                     delete_after=10)
        elif isinstance(error, discord.errors.Forbidden):
            message = await ctx.send("I do not have the necessary permissions to perform this command.",
                                     delete_after=10)
        elif isinstance(error, commands.CommandOnCooldown):
            message = await ctx.send(f"This command is on a {round(error.retry_after, 2)}s cooldown",
                                     delete_after=error.retry_after)
        elif isinstance(error, commands.CommandNotFound):
            message = await ctx.send(*error.args, delete_after=10)
            similar_command = await correct_command_name(self.bot, ctx, ctx.invoked_with)
            if similar_command:
                await ctx.send(f'Maybe you mean **`{similar_command}`** ?', delete_after=15)
        elif isinstance(error, commands.errors.BadArgument):
            pass
        else:
            tb = traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__)
            traceback_fmt = ''.join(tb)
            owner_id = self.bot.owner_id or (await self.bot.application_info()).owner.id
            await ctx.send(f'<@{owner_id}>\n'
                           f'```python\n'
                           f'{traceback_fmt}'
                           f'```')
            message = await ctx.send(f'```python\n'
                                     f'{" ".join(error.args)}\n\n'
                                     f'{ctx.message.clean_content = }\n'
                                     f'{ctx.message.content = }\n\n'
                                     f'{ctx.command.cog.qualified_name = }\n'
                                     f'{ctx.command.name = }\n\n'
                                     f'{ctx.invoked_with = }\n\n'
                                     f'{ctx.invoked_parents = }\n'
                                     f'{ctx.invoked_subcommand = }\n'
                                     f'{ctx.subcommand_passed = }\n\n'
                                     f'{ctx.kwargs = }```')


def setup(bot):
    bot.add_cog(Errors(bot))

import random

from discord.ext import commands

from log import Logger

from ..bot import CustomBot


class Games(commands.Cog):
    """ Commands that deal with games! """

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.command(help="Rolls the dice, ranging from either 1 to some target number.")
    async def rtd(self, ctx: commands.Context, target: int = 10):
        """ 
        Rolls the dice and randomly generates a number from start to some target number. 
        Default target number is 10. 
        """
        try:
            number = str(random.randint(1, target))
            await Logger.CTX_INFO(ctx, f"Rolled `{number}`")
        except Exception as e:
            await Logger.CTX_ERROR(ctx, f"Error with rolling dice: {e}")


async def setup(bot: CustomBot):
    await bot.add_cog(Games(bot))

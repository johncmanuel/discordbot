import discord
from discord.ext import commands

from ..bot import CustomBot


class Interact(commands.Cog):
    """ Interactions with the bot. """

    def __init__(self, bot: CustomBot):
        self.bot = bot
        self.database = self.bot.database

    @commands.command(aliases=['spamming'], help="Spam someone :D", hidden=True)
    @commands.is_owner()
    async def spam(self, ctx: commands.Context, player: discord.Member = None, nums: int = 5):
        for i in range(nums):
            await ctx.send(player.mention)


async def setup(bot: CustomBot):
    await bot.add_cog(Interact(bot))

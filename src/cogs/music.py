from discord.ext import commands

from ..bot import CustomBot


class Music(commands.Cog):
    """ Commands that deal with music """

    def __init__(self, bot: CustomBot):
        self.bot = bot
        self.music_queue = []

    # @commands.command(name="p")
    # async def play(self, ctx: commands.Context):
    #     pass

    # async def pause(self, ctx: commands.Context):
    #     pass

    # async def resume(self, ctx: commands.Context):
    #     pass

    # async def skip(self, ctx: commands.Context):
    #     pass

    # async def queue(self, ctx: commands.Context):
    #     pass

    # async def volume(self, ctx: commands.Context):
    #     pass


async def setup(bot: CustomBot):
    await bot.add_cog(Music(bot))

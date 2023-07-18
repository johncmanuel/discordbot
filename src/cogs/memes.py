import io
from datetime import datetime
from typing import List, Union

import discord
from discord.ext import commands

from config import TIMEZONE
from log import Logger
from src.bot import CustomBot

from ..utils.imageUtils import ImageText


class Memes(commands.Cog):
    """ Commands where the user can create memes within Discord using the bot. """

    # Accessing the coordinates requires the name of the command being
    # invoked
    # TODO: Instead of hardcoding coords, add them to the database
    coords = {
        "small": [(90, 190), (361, 270)],
        "aye": [(20, 80), (20, 320), (20, 553)],
    }

    def __init__(self, bot) -> None:
        self.bot = bot
        self.font_name = "./src/fonts/Anton-Regular.ttf"

    def get_binary_img(self, img: ImageText, user: str, guild: str) -> discord.File:
        """ 
        Turns an image into a bytes object and packages it into a 
        Discord File
        """
        curr_time = datetime.now(tz=TIMEZONE).strftime("%Y%m%d")
        with io.BytesIO() as binary_img:
            img.save(binary_img)
            binary_img.seek(0)
            return discord.File(fp=binary_img, filename=f'{curr_time}_tyler1meme_{user}_{guild}.png')

    @staticmethod
    def get_captions(message: str, delim: str = ';') -> List[str]:
        """ 
        Splits the message into a list each containing a 
        caption for the meme 
        """
        user_input = message.split(delim)
        captions = [caption.strip() for caption in user_input if caption != '']
        return captions

    async def write_text_to_img(
            self, ctx: commands.Context,
            img_path: str, captions: str,
            box_width: int, font_color: str = 'black',
            font_size: int = 20, place: str = 'center') -> Union[discord.File, None]:
        """ 
        Writes text at a specific coordinate in the meme 
        template image and returns it as a bytes object packed
        into a Discord File.
        """
        l_captions = self.get_captions(captions)
        img = ImageText(img_path, background=(255, 255, 255, 200))
        coords = self.coords[ctx.command.name]

        # The number of captions must match the number of coordinates
        if len(coords) == len(l_captions):
            for coord, caption in zip(coords, l_captions):
                img.write_text_box(
                    xy=coord,
                    text=caption,
                    box_width=box_width,
                    font_filename=self.font_name,
                    font_size=font_size,
                    color=font_color,
                    place=place
                )
            meme = self.get_binary_img(
                img, user=ctx.author.name, guild=ctx.guild.name)
            return meme
        else:
            await Logger.CTX_ERROR(ctx, f"There needs to be at least {len(coords)} captions.")
            return None

    async def send_meme(self, ctx: commands.Context, meme: discord.File) -> None:
        await ctx.send(file=meme) if meme is not None else None

    @commands.command(help="Creates a meme based on the short Tyler1 meme.")
    async def small(self, ctx: commands.Context, *, arg) -> None:
        meme = await self.write_text_to_img(
            ctx,
            img_path='./src/imgs/shortMeme.png',
            captions=arg,
            box_width=100,
            font_color='yellow')
        await self.send_meme(ctx, meme)

    @commands.command(
        help="Creates a meme based on Tyler1 being progressively scared. In order to use, separate each caption with a delimiter (by default, ';')")
    async def aye(self, ctx: commands.Context, *,
                  arg=commands.parameter(description="Your set of captions. Be sure to separate each one with ';'")) -> None:
        meme = await self.write_text_to_img(
            ctx,
            img_path='./src/imgs/ayeMeme.png',
            captions=arg,
            box_width=270)
        await self.send_meme(ctx, meme)


async def setup(bot: CustomBot):
    await bot.add_cog(Memes(bot))

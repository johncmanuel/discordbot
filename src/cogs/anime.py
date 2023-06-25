""" TO BE WORKED ON FURTHER. """

import traceback
from ast import literal_eval

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

try:
    from urllib import urlencode

    import urlparse
except:  # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode

# Most, if not, probably all functions are based off IGRohan's functions:
# https://github.com/IGRohan/AnimeAPI/blob/main/scraper/animixplay/animixplay.js
animix_base = "https://animixplay.to/"
animix_search_api_2 = "https://v1.ij7p9towl8uj4qafsopjtrjk.workers.dev/"
# animix_all = "https://animixplay.to/assets/s/all.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
browser_headers = {
    "User-Agent": USER_AGENT
}
# Why I need this constant
# https://discordpy.readthedocs.io/en/stable/api.html?highlight=embed#discord.Embed
EMBED_SIZE_LIMIT = 6000


class Anime(commands.Cog):
    """ Commands that deal with fetching anime episodes """

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(
            loop=bot.loop, raise_for_status=True)

    @commands.command(name="search")
    async def search_animix(self, ctx, *args):
        """ Search the AniMix database using the provided keyword. """
        # Get all arguments from command input and combine them into one keyword
        keyword = ' '.join(args)
        # Search AniMix using a keyword to get results
        try:
            if not keyword:
                await ctx.send(f'{ctx.author.mention}: No keyword provided.')
                return
            data = None
            anime = []
            async with self.session.post(url=animix_search_api_2, headers=browser_headers, data=urlencode({"q2": keyword})) as res:
                data = await res.json()
            if data is not None:
                soup = BeautifulSoup(data['result'], 'lxml')
                li_items = soup.find('ul')
                anime = [{
                    "anime_title": li.find('a')['title'],
                    "anime_id": li.find('a')['href'].replace('/v1/', '')}
                    for li in li_items.find_all('li')
                ]
                # Pack the data into a Discord Embed and send it to the author
                embed = discord.Embed(title=f'"{keyword}"')
                embed.set_author(name=ctx.author.display_name,
                                 icon_url=ctx.author.avatar_url)
                # If no searches are found, send this in the embed.
                if len(anime) == 0:
                    embed.add_field(name="No results found.", value=":(")
                else:
                    for i in range(len(anime)):
                        embed.add_field(
                            name=f"{i+1}: {anime[i]['anime_title']}", value=f"anime_id: {anime[i]['anime_id']}")
                await ctx.send(embed=embed)
        except Exception:
            await ctx.send(f'{ctx.author.mention}: {traceback.format_exc()}')

    @commands.command(name="ep")
    @commands.cooldown(5.0, 15.0, commands.BucketType.guild)
    async def fetch_recent_anime_episodes(self, ctx, anime_id, recent_episodes_length=5):
        """ Use the anime_id generated from *search* to fetch the latest episodes of that respective anime. """
        if not anime_id:
            await ctx.send("Invaid anime_id.")
            return
        try:
            res = await self.session.get(url=f'{animix_base}v1/{anime_id}', headers=browser_headers)
            # This beautiful one-liner converts a string representation of a dictionary into an actual
            # dictionary. The dictionary was a string at first since I turned the response into a string using
            # .text()
            # https://stackoverflow.com/questions/988228/convert-a-string-representation-of-a-dictionary-to-a-dictionary
            episodes = literal_eval((BeautifulSoup(await res.text(), 'lxml').find('div', {'id': 'epslistplace'}).contents)[0])
            # print(type(episodes), episodes)
            eptotal = episodes["eptotal"]
            recent_episodes = []
            # Add episodes based on how much recent episodes if eptotal is bigger
            if recent_episodes_length < eptotal:
                recent_episodes = [{i+1: episodes[str(i)].replace('//', '')}
                                   for i in range(eptotal-recent_episodes_length, eptotal)]
            # Add all the episodes by length of eptotal if the length of recent episodes specified is more than eptotal
            else:
                recent_episodes = [
                    {i+1: episodes[str(i)].replace('//', '')} for i in range(eptotal)]
            # Create Discord embed
            embed = discord.Embed(title=anime_id)
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.avatar_url)
            # Add episode and link to episode for each embed fields
            for item in recent_episodes:
                for key in item:
                    embed.add_field(
                        name=f"episode {key}", value=f"[LINK](https://{item[key]})")
            # Remove field(s) to prevent embed size from exceeding 6000 characters
            # if len(embed) > EMBED_SIZE_LIMIT:
            #     for i in range(len(embed)-1):
            #         # Keep removing fields until the length of the embed is less than the limit
            #         embed.remove_field(i)
            #         if len(embed) < EMBED_SIZE_LIMIT:
            #             break
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(f'{ctx.author.mention}: {traceback.format_exc()}')


async def setup(bot):
    await bot.add_cog(Anime(bot))

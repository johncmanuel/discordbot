""" TO BE WORKED ON FURTHER """

# import aiohttp
import datetime
import os
import random

from discord.ext import commands
from riotwatcher import LolWatcher

from config import PROJ_CACHE_PATH, TIMEZONE
from log import Logger

from ..bot import CustomBot
from ..utils.helper import Helper, JSONHelper
from ..utils.http_utils import HTTPClient

# Maps the player to their respective roles
# (lane, role): player role
PLAYER_ROLE_MAP = {
    ('MIDDLE', 'SOLO'): 'Middle',
    ('TOP', 'SOLO'): 'Top',
    ('JUNGLE', 'NONE'): 'Jungle',
    ('BOTTOM', 'CARRY'): 'ADC',
    ('BOTTOM', 'SUPPORT'): 'Support',
    # ('BOTTOM', 'DUO'): 'ADC',
    # ('BOTTOM', 'DUO_SUPPORT'): 'Support',
}


class LeagueAPI():
    """ Wrapper class around Riotwatcher, a League of Legends API wrapper library """

    def __init__(self, region: str = 'na1') -> None:
        self.watcher = LolWatcher(os.getenv('RIOT_API_KEY'))
        self.region = region
        self.DATA_DRAGON_URL = "https://ddragon.leagueoflegends.com"
        self.VERSION_URL = f"{self.DATA_DRAGON_URL}/api/versions.json"
        self.LANGUAGES_URL = f"{self.DATA_DRAGON_URL}/cdn/languages.json"

    def get_summoner(self, name: str):
        """ Get the summoner given the name """
        return self.watcher.summoner.by_name(region=self.region, summoner_name=name)

    def get_puuid(self, summoner) -> str:
        """ Get the PUUID of the summoner """
        return summoner['puuid']

    def get_matches_with_puuid(self, player_puuid: str, queue: int = 420, count: int = 10):
        """ Get a number of matches of the player. 

        queue ids:
        - 400 (5v5 normal draft),
        - 420 (5v5 ranked solo/duo),
        - 430 (5v5 normal blind),
        - 440 (5v5 ranked flex)
        See http://static.developer.riotgames.com/docs/lol/queues.json for more types.
        """
        # TODO: Allow multiple queue types and return a collection of matches with different
        # queue types.
        return self.watcher.match.matchlist_by_puuid(
            region=self.region,
            puuid=player_puuid,
            queue=queue,
            count=count
        )

    def get_match_by_match_id(self, match_id: str):
        return self.watcher.match.by_id(region=self.region, match_id=match_id)

    def get_current_champion_list(self, want_full: bool = False):
        versions = self.watcher.data_dragon.versions_for_region(self.region)
        champion_verison = versions['n']['champion']
        return self.watcher.data_dragon.champions(champion_verison, full=want_full)

    def get_summoner_data(self, name: str):
        return self.watcher.league.by_summoner(
            self.region,
            self.get_summoner(name=name)['id']
        )


class League(commands.Cog):
    """ All commands related to League of Legends. """

    def __init__(self, bot: CustomBot):
        self.bot = bot
        self.watcher = LeagueAPI()
        self.league_cache = f"{PROJ_CACHE_PATH}/{__class__.__name__}"
        self.CHAMPIONS_PATH = f"{self.league_cache}/champion.json"
        # self.patch.start()

    async def _get_version(self):
        """ 
        Returns the current version of League of Legends.
        Example response (source: https://ddragon.leagueoflegends.com/api/versions.json):
        [ "13.9.1", "13.8.1", "13.7.1", ...]
        """
        async with HTTPClient(loop=self.bot.loop, name=Helper.get_func_name()) as session:
            data = await session.get(self.watcher.VERSION_URL)
            data = await data.json()
        Logger.DEBUG("Got version!")
        version = data[0]
        return version if version is not None else None

    async def _get_language(self, specified_lang: str):
        """ 
        Returns a language specified in the JSON response.
        See full list here:
        https://developer.riotgames.com/docs/lol#data-dragon_languages
        """
        async with HTTPClient(loop=self.bot.loop, name=Helper.get_func_name()) as session:
            Logger.DEBUG("Beginning to retrieve lang data...")
            data = await session.get(self.watcher.LANGUAGES_URL)
            data = await data.json()
        Logger.DEBUG("Got language!")
        for lang in data:
            if specified_lang == lang:
                return lang
        return None

    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    @commands.command(brief="Displays basic stats from League.", description="Displays basic stats from League. \n\nNote that the region is set to NA." +
                      " This does not support other regions at the moment.\n\nIn the usage below, also note that [args...] enables this command to accept names with spaces.\n\n" +
                      ">stats only records ranked data! This command is useful for those who usually play ranked.")
    async def stats(self, ctx: commands.Context, summoner: str, *args) -> None:
        """ Function that displays stats on League. """
        full_name = Helper.combine_strings(args, summoner)
        Logger.DEBUG(f"Gathering stats on player {full_name}...")
        # Example output:
        # {'leagueId': '64de6776-701d-3731-9884-9f22c07f5e6b', 'queueType': 'RANKED_SOLO_5x5', 'tier': 'MASTER', 'rank': 'I',
        # 'summonerId': 'NTT0wwspSKfXamq451ReBqRSLr_mqWZuKOtvcC8t65sV5kA', 'summonerName': 'Doublelift', 'leaguePoints': 336,
        # 'wins': 88, 'losses': 91, 'veteran': False, 'inactive': False, 'freshBlood': False, 'hotStreak': False}
        summoner_data = self.watcher.get_summoner_data(full_name)[0]
        Logger.DEBUG(summoner_data)

        if len(summoner_data) == 0 or summoner_data is None:
            await ctx.send(f"No data available for {full_name}")
            return

        # NOTE: Identation is like that on purpose.
        await ctx.send(
            f"""
Name: {summoner_data['summonerName']}
Wins: {summoner_data['wins']}
Losses: {summoner_data['losses']}

Rank: {summoner_data['tier'].title()} {summoner_data['rank']}
League Points (LP): {summoner_data['leaguePoints']} 
            """
        )

    @commands.cooldown(5.0, 10.0, commands.BucketType.guild)
    @commands.command(brief="Pulls data from 10 recent League of Legends (normal/ranked) games.", description="Pulls data from 10 recent League of Legends (normal/ranked) games.\n\nNote that the region is set to NA." +
                      " This does not support other regions at the moment.\n\nIn the usage below, also note that [args...] enables this command to accept names with spaces.")
    async def matches(self, ctx: commands.Context, summoner: str, *args) -> None:
        summoner_name = Helper.combine_strings(args, summoner)
        summoner_info = self.watcher.get_summoner(summoner_name)
        player_puuid = self.watcher.get_puuid(summoner_info)
        matches = self.watcher.get_matches_with_puuid(
            player_puuid=player_puuid)

        Logger.INFO(f"Activating {__name__}")
        Logger.DEBUG(
            f"summoner: {summoner_name} | summoner PUUID: {summoner_info}")
        Logger.DEBUG(f"matches: {matches}")

        # This will be deleted later after the data is loaded
        loading = await ctx.send(f'Loading summoner {summoner_name}...')

        # Store all player data from each match. Each piece of player
        # data is formatted as a dictionary
        data = []

        # Iterate through each match
        for match_id in matches:
            player_match_data = self.watcher.get_match_by_match_id(match_id)
            match_info = player_match_data["info"]

            # Get the participant's data if their PUUID matches in the data
            player_data = next((item for item in match_info["participants"] if item.get(
                "puuid") == player_puuid), None)
            if player_data is None:
                Logger.DEBUG(f"Match data for {summoner_name} was not found!")

            Logger.DEBUG(f"player_data: {player_data}")

            # Set up a dictionary to store the player's information during that
            # match and append it to "data" list
            tmp = {}
            tmp['championName'] = player_data['championName']
            tmp['kills'] = player_data['kills']
            tmp['assists'] = player_data['assists']
            tmp['deaths'] = player_data['deaths']
            tmp['kda'] = round(player_data['challenges']['kda'], ndigits=2)
            tmp['win'] = player_data['win']
            tmp['role'] = 'N/A'

            # Get rid of the miliseconds
            tmp['date'] = match_info["gameCreation"] / 1000

            # If role matches what API gives, set the role
            role = (player_data['lane'], player_data['role'])
            if role in PLAYER_ROLE_MAP:
                tmp['role'] = PLAYER_ROLE_MAP[role]

            # Ensure that data being appended is nonempty
            if len(tmp.keys()) != 0:
                data.append(tmp)

        Logger.DEBUG(f"tmp: {data}")

        # Combine each match's stats into one string and send it to the user
        player_stats = ''
        kills = deaths = assists = kda = 0
        for count, match in enumerate(data):
            stats = '\n\nMatch #{count} — Date: {date}\nChampion: {champ_name}\nKills: {kills}\nDeaths: {deaths}\nAssists: {assists}\nRole: {role}'.format(
                champ_name=match['championName'],
                kills=match['kills'],
                deaths=match['deaths'],
                assists=match['assists'],
                role=match['role'],
                count=count + 1,
                date=datetime.datetime.fromtimestamp(
                    match['date'], tz=TIMEZONE).strftime('%m-%d-%y %a %I:%M:%S %p')
            )
            # Sum the kills, deaths, and assists to get total amount for each stat
            # out of the matches given
            kills += match['kills']
            deaths += match['deaths']
            assists += match['assists']

            player_stats += stats

        # Prevent division by zero
        kda = round(((kills + assists) / deaths),
                    2) if deaths != 0 else kills + assists

        await loading.delete()
        await Logger.CTX_INFO('```' +
                              f'Summoner: {summoner_name}\n\n' +
                              player_stats +
                              f'\n\nTotal kills: {kills}\n' +
                              f'Total deaths: {deaths}\n' +
                              f'Total assists: {assists}\n' +
                              f'Total KDA (across these matches): {kda}\n' +
                              '```')

    # TODO: Rework the patch notes posting automation some time later
    # @tasks.loop(hours=1.0)
    # async def patch(self):
    #     from bs4 import BeautifulSoup

    #     # Ensures that the loop doesn't run immediately after bot offically starts running.
    #     if self.patch.current_loop != 0:

    #         GUILD = os.getenv('DISCORD_GUILD')

    #         lolWebsite = "https://na.leagueoflegends.com"
    #         patchUrl = 'https://wrapapi.com/use/johnm01/lol/patch/1.0.0?wrapAPIKey=' + WRAPAPI_KEY
    #         browserheaders = {
    #             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
    #             "like Gecko) Chrome/64.0.3257.0 Safari/537.36"}

    #         content = None

    #         async with self.session.get(patchUrl, headers = browserheaders) as response:
    #             if response.status == 200:
    #                 content = await response.text()

    #         # lxml is the fastest HTML parser, according to the docs.
    #         # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    #         soup = BeautifulSoup(content, "lxml")

    #         links = []
    #         imgs = []
    #         titles = []

    #         # Append the html tags from each element into their respective lists.
    #         def appendElems(elements, listToAppendTo, tag):
    #             for element in elements:
    #                 # Removes the double slashes and extra quotes around link
    #                 # and stores them into a list
    #                 listToAppendTo.append(element.get(tag).translate(str.maketrans({'\\': '', '"': ''})))

    #         appendElems(soup.findAll('a'), links, 'href')
    #         appendElems(soup.findAll('img'), imgs, 'src')

    #         # Get name of the patch notes
    #         for title in soup.findAll('h2'):
    #             titles.append(title.text.strip().title())

    #         # Remove dupes from imgs list
    #         # thank you https://stackoverflow.com/questions/7961363/removing-duplicates-in-the-lists so much.
    #         imgsWithoutDupes = list(dict.fromkeys(imgs))

    #         data = [{'title': title, 'link': link, 'img': img} for title, link, img in zip(titles, links, imgsWithoutDupes)]

    #         # Dump the patch notes in a JSON so it can be compared to the API
    #         # response
    #         if self.checkIfFileExists('patchNotes.json') is False:
    #             self.createEmptyJSON('patchNotes.json')
    #             with open('patchNotes.json', 'w') as outfile:
    #                 json.dump(data, outfile, indent=2)
    #                 print('sup')

    #         getPatchNotesFromJSON = self.getJSON('patchNotes.json')

    #         print(getPatchNotesFromJSON)

    #         # If there's a new patch, update the JSON file and send the new data
    #         # to a dedicated text channel for output.
    #         if data[0] != getPatchNotesFromJSON[0]:
    #             with open('patchNotes.json', 'w') as outfile:
    #                 json.dump(data, outfile, indent=2)

    #             # We want the latest patch notes so access the first elements here
    #             newestPatchUrl = lolWebsite + data[0]['link']
    #             imageUrl = data[0]['img']
    #             patchTitle = data[0]['title']

    #             # Create embed and send it
    #             embed = discord.Embed(color=discord.Color.gold(), description=f'Latest League of Legends Patch Notes: {newestPatchUrl}')
    #             embed.set_image(url=imageUrl)
    #             embed.set_author(
    #                 name='League of Legends: ' + patchTitle,
    #                 url=newestPatchUrl,
    #                 icon_url="http://2.bp.blogspot.com/-HqSOKIIV59A/U8WP4WFW28I/AAAAAAAAT5U/qTSiV9UgvUY/s1600/icon.png",
    #             )

    #             # It's good for one guild, but not for many. Since this function will be a
    #             # background task, I won't be able to use ctx.
    #             guild = discord.utils.get(self.bot.guilds, name=GUILD)

    #             name = 'league-patch-notes'
    #             channel = discord.utils.get(guild.text_channels, name=name)

    #             if channel is None:
    #                 print('no channel')
    #                 channel = await guild.create_text_channel(
    #                             name,
    #                             position=len(guild.text_channels),
    #                             topic="An automated text channel that provides League of Legends patch notes to the server.")

    #             await channel.send(embed=embed)

    #         print('patch loop complete! times finished:', self.patch.current_loop)

    # @patch.before_loop
    # async def beforePatch(self):
    #     print('patch background task: waiting for bot to start...')
    #     await self.bot.wait_until_ready()

    # def cog_unload(self):
        # self.patch.cancel()

    @commands.cooldown(5.0, 10.0, commands.BucketType.guild)
    @commands.command(aliases=["unboxing"], brief="Randomly unboxes a skin.", description="Randomly unboxes a skin.")
    async def unbox(self, ctx: commands.Context) -> None:
        """ 
        Simulates Hextech Chest unboxing from League. 
        It only outputs skins, not essence or anything else at the moment. 
        """
        champions_data = None
        version = await self._get_version()
        lang = await self._get_language(specified_lang="en_US")
        CHAMPS_URL = self.watcher.DATA_DRAGON_URL + \
            f"/cdn/{version}/data/{lang}/champion.json"
        Logger.DEBUG(f"URL to champion JSON file: {CHAMPS_URL}")
        async with HTTPClient(loop=self.bot.loop, name=Helper.get_func_name()) as session:
            res = await session.get(CHAMPS_URL)
            res = await res.json()

        Helper.mkdir(self.league_cache)

        # Use the cached response instead if it exists. Else, create one
        # and cache it.
        if Helper.path_contains_valid_file(self.CHAMPIONS_PATH):
            Logger.DEBUG(
                f"Path {self.CHAMPIONS_PATH} exists! Retrieving cached response...")
            champions_data = JSONHelper.get_json_as_dict(self.CHAMPIONS_PATH)

            # TODO: Make a task to routinely update the cached champions list every day.
            # That way, this would reduce need to fetch res every time this command is called.
            if res['version'] != champions_data['version']:
                Logger.DEBUG(f"{res['version']}, {champions_data['version']}")
                Logger.DEBUG('version does not match, updating file now')
                JSONHelper.cache_response(res, self.CHAMPIONS_PATH)
                champions_data = JSONHelper.get_json_as_dict(
                    self.CHAMPIONS_PATH)

        # This would occur only once if this program is being set up for the
        # first time. After it's set up, this will most likely not be executed ever,
        # unless the cached response is deleted for some reason.
        else:
            Logger.DEBUG(self.CHAMPIONS_PATH)
            JSONHelper.cache_response(res, self.CHAMPIONS_PATH)
            champions_data = JSONHelper.get_json_as_dict(self.CHAMPIONS_PATH)

        # Get all the champion names in League of Legends
        champions_data = list(champions_data["data"].keys())
        Logger.DEBUG(f"champion names: {champions_data}")
        random_champ = random.choice(champions_data)

        # Get URL to a randomly chosen champion's data and fetch it
        CHAMP_URL = self.watcher.DATA_DRAGON_URL + \
            f"/cdn/{version}/data/{lang}/champion/{random_champ}.json"
        Logger.DEBUG(f"Champion selected: {random_champ}, {CHAMP_URL}")
        async with HTTPClient(loop=self.bot.loop, name=Helper.get_func_name()) as session:
            random_champ_data = await session.get(CHAMP_URL)
            random_champ_data = await random_champ_data.json()

        skins = random_champ_data["data"][random_champ]["skins"]
        Logger.DEBUG(f"Retrieved skins for {random_champ}!")

        # Want to start from 1 because the user shouldn't win default
        # skins.
        random_skin = random.randint(1, len(skins)-1)
        random_skin = skins[random_skin]
        Logger.DEBUG(f"Random skin picked: {random_skin}")

        # The URL was found using the random champion's name and the ID of the random skin.
        # See more: https://developer.riotgames.com/docs/lol#data-dragon_champion-splash-assets
        skin_splash_art_img_url = f"""
        http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{random_champ}_{str(random_skin['num'])}.jpg"""
        Logger.INFO(f"Skin for {random_champ} retrieved")

        # Send the results to the user
        await ctx.send(skin_splash_art_img_url)
        await Logger.CTX_SUCCESS(ctx, f"Congratulations, you won: **{random_skin['name']}**")


async def setup(bot: CustomBot):
    await bot.add_cog(League(bot))

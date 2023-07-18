import asyncio
import os

from discord import __version__

from config import BOT_DESC, DISCORD_COGS_PATH, EXCLUDED_COGS, PROJ_CACHE_PATH
from log import Logger
from src.bot import CustomBot
from src.subsystems.firebase_auth import FirebaseAuth
from src.subsystems.sys_assets_storage import AssetsStorage
from src.subsystems.sys_firebase import Database
from src.utils.helper import Helper


class Application():
    """ Main application entry point for the bot """

    def __init__(self) -> None:
        """ Initialize bot and other components of the application """
        Logger.INFO("Logger initiated")
        Logger.DEBUG(f"discord.py version: {__version__}")

        self.firebase_auth = FirebaseAuth()
        Logger.INFO("Authenticated with Google Firebase.")

        self.database = Database()
        Logger.INFO("Authenticated with Google Realtime Database.")

        self.assets_storage = AssetsStorage()
        Logger.INFO("Authenticated with Google Cloud Storage.")

        # Create cache folder for storing local files
        Helper.mkdir(PROJ_CACHE_PATH)
        Logger.INFO(f"Created {PROJ_CACHE_PATH}")

        self.bot = CustomBot(
            p_description=BOT_DESC,
            database=self.database,
            assets_storage=self.assets_storage,
        )
        Logger.INFO("Running bot")

    def get_bot(self):
        """ Returns instance of the bot """
        return self.bot

    async def _start_bot(self) -> None:
        """ Runs the bot from the Application level """
        async with self.bot:
            await self.bot.start_bot()

    async def _close_bot(self) -> None:
        """ Closes the bot """
        await self.bot.close_bot()

    async def setup_cogs(self) -> None:
        """ 
        Sets up cogs by searching and loading folder with cogs files (.py files).
        Source for solution: 
        https://stackoverflow.com/questions/65203363/how-to-load-multiple-cogs-in-python-3
        """
        if __name__ == '__main__':
            for filename in os.listdir(DISCORD_COGS_PATH):
                filename_without_ext = Helper.strip_file_ext(
                    f"{DISCORD_COGS_PATH}/{filename}")
                if filename.endswith(".py") and filename_without_ext not in EXCLUDED_COGS:
                    Logger.DEBUG(f"Now loading cog: {filename}")
                    cog_file = f"{DISCORD_COGS_PATH}.{filename[:-3]}".lstrip("./").replace(
                        "/", ".")
                    await self.bot.load_extension(cog_file)
                    Logger.DEBUG(f"Loaded cog: {filename}")


# Instead of running the application synchronously, run it asynchronously
# https://discordpy.readthedocs.io/en/stable/migrating.html#asyncio-event-loop-changes
async def main():
    app = Application()
    bot = app.get_bot()
    async with bot:
        await app.setup_cogs()
        await bot.start_bot()

asyncio.run(main())

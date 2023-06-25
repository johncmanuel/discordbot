import discord
from discord.ext import commands, tasks

from log import Logger

from ..bot import CustomBot
from ..utils.helper import Helper


class Voice(commands.Cog):
    """ Voice-related commands for the bot. """

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.assets_storage = self.bot.assets_storage
        self.voice_manager = self.bot.voice_manager
        self.voice_cache_path = self.assets_storage.audio_cache_path
        self.clean_audio_cache.start()

    @tasks.loop(hours=24)
    async def clean_audio_cache(self):
        """ 
        In case audio cache files are not removed, routinely
        clean the directory.
        """
        Helper.remove_directory_contents(self.voice_cache_path)

    def cog_unload(self):
        self.clean_audio_cache.cancel()

    def _get_voice_and_channel(self, ctx: commands.Context):
        voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel
        return voice, channel

    @commands.command(name="getobjs")
    async def get_objs_names(self, ctx: commands.Context, folder_name: str = None) -> None:
        paths, folders = self.assets_storage.list_blobs_as_str(
            prefix=folder_name)
        paths_str = f"List of files in `{folder_name}` available in the cloud: ```{paths}```\n"
        folders_str = f"Folders found in `{folder_name}`: ```{folders}```"
        if len(paths) == 0:
            paths_str = f"No files found in path `{folder_name}`!\n"
        if len(folders) == 0:
            folders_str = f"No folders found in path `{folder_name}`!\n"
        info = f"{paths_str}{folders_str}"
        await Logger.CTX_INFO(ctx, info)

    @commands.command(name="getdirs")
    async def get_directories(self, ctx: commands.Context, folder: str = None) -> None:
        """ Gets directories from storage """
        message = self.assets_storage.list_bucket_directories_as_str(folder)
        await Logger.CTX_INFO(ctx,
                              f"List of directories in cloud: ```{message}```")

    @commands.command(name="pclip")
    async def play_clip_from_audio_blob(self, ctx: commands.Context, audio_clip_name: str) -> None:
        is_downloaded = self.assets_storage.get_audio_file(audio_clip_name)
        if not is_downloaded:
            Logger.CTX_ERROR(f"Audio clip `{audio_clip_name}` not found.")
            return
        voice, channel = self._get_voice_and_channel(ctx)
        await self.voice_manager.join_channel_and_play_clip(
            voice, channel, self.assets_storage.audio_file_path)
        self.assets_storage.remove_audio_file()

    @commands.command(name="rclip")
    async def play_random_clip_from_audio_blob(self, ctx: commands.Context):
        random_clip, random_clip_name = self.assets_storage.get_random_blob(
            prefix="audio/")
        Logger.DEBUG(random_clip_name)
        if not random_clip_name:
            await Logger.CTX_ERROR(ctx, "Can't find a valid audio file. Maybe there aren't any audio files?")
            return
        self.assets_storage.download_audio_file(random_clip, random_clip_name)
        voice, channel = self._get_voice_and_channel(ctx)
        await self.voice_manager.join_channel_and_play_clip(
            voice, channel, self.assets_storage.audio_file_path)
        self.assets_storage.remove_audio_file()


async def setup(bot: CustomBot):
    await bot.add_cog(Voice(bot))

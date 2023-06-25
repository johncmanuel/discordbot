from io import BytesIO

import aiohttp
import discord
from discord.ext import commands
from PIL import Image

from config import ADMIN_ROLE, BOT_SETTINGS_PATH
from log import Logger

from ..bot import CustomBot
from ..utils.helper import Helper
from ..utils.http_utils import HTTPClient


class Admin(commands.Cog):
    """ Commands that deal with administrative properties and tasks """

    def __init__(self, bot: CustomBot):
        self.bot = bot
        self.database = self.bot.database
        self.assets_storage = self.bot.assets_storage

    @commands.command(name='setprefix', aliases=['changeprefix', 'change_prefix', 'changePrefix'], 
                      help='Change prefix for commands.')
    @commands.is_owner()
    @commands.guild_only()
    async def change_cmd_prefix(self, ctx: commands.Context, new_cmd_prefix: str):
        """ Change command prefix (ex. '>' or '!') """
        if len(new_cmd_prefix) > 1:
            await Logger.CTX_ERROR(ctx, "Prefix must be a single character!")
            return
        data = self.database.read(BOT_SETTINGS_PATH)
        for key in data:
            self.database.update(BOT_SETTINGS_PATH, {
                key: {'cmd_prefix': new_cmd_prefix}
            })
            await Logger.CTX_SUCCESS(ctx, f"Changed command prefix to `{new_cmd_prefix}`")
            break

    ###################################################
    # The following commands are derived from Alex Flipnote:
    # https://github.com/AlexFlipnote/discord_bot.py/blob/a504d8dfbfac3248f529d53c2bca210f86e37a87/cogs/admin.py

    @commands.command(name='setname', aliases=['nickname'], help="Change bot's nickname.")
    @commands.has_any_role(ADMIN_ROLE)
    async def change_nickname(self, ctx: commands.Context, *, name: str = None):
        """ Change nickname of the bot """
        if name is None:
            await Logger.CTX_ERROR(ctx, "No name provided...")
            return
        me = ctx.guild.me
        old_nickname = me.nick
        await me.edit(nick=name)
        if name:
            await Logger.CTX_SUCCESS(ctx, f"Changed nickname from `{old_nickname}` to `{name}`!")
        else:
            await Logger.CTX_SUCCESS(ctx, "Removed nickname!")

    @commands.command(name='setavatar', help="Change bot's avatar")
    @commands.has_any_role(ADMIN_ROLE)
    async def change_avatar(self, ctx: commands.Context, url: str = None):
        """ Change bot's avatar using a valid image URL """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip("<>") if url else None
        try:
            Logger.DEBUG(f"url: {url}")
            func_name = Helper.get_func_name()
            async with HTTPClient(loop=self.bot.loop, name=func_name) as session:
                async with session.get(url) as r:
                    img = Image.open(BytesIO(await r.read()), mode='r')
                    with BytesIO() as b:
                        img.save(b, format="PNG")
                        await self.bot.user.edit(avatar=b.getvalue())
            await Logger.CTX_SUCCESS(ctx, f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await Logger.CTX_ERROR(ctx, "The URL is invalid...")
            return

    @commands.command(help="Let the bot direct message (DM) a user of your choice.")
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user: discord.User, *, message: str):
        """ DM the user of your choice """
        try:
            await user.send(message)
            await ctx.author.send(f"✉️ Succesfully sent a fan letter to **{user}**!")
            await ctx.author.send(f"Contents of messsage: {message}")
            # Delete the message after issuing the command 
            await ctx.message.delete()
        except discord.Forbidden:
            await Logger.CTX_ERROR(ctx, "This user might have their DMs blocked or it's a bot account.")

    ###################################################

    ###################################################
    # NOTE:
    # Custom activities don't work due to limitations on Discord's end
    # https://github.com/Rapptz/discord.py/issues/2400#issuecomment-546757644
    #
    # Not sure why it's implemented if it can't work for bots. Maybe there is a way,
    # unless I'm not up to date with Discord API's
    # https://discord.com/developers/docs/topics/gateway#activity-object-activity-types

    @commands.command(name="setstatus")
    @commands.has_any_role(ADMIN_ROLE)
    async def change_bot_presence(self, ctx: commands.Context, status: str, 
                                  *, text: str = None) -> None:
        """ 
        Change the presence of the bot.
        The choices for parameter status are the following:
        1. streaming
        2. playing
        3. listening
        4. watching

        May want to refer to the docs here for understanding each type of presence:
        https://discordpy.readthedocs.io/en/stable/api.html?highlight=discord%20streaming#activity
        """
        status = status.lower()
        if text is None:
            await Logger.CTX_ERROR(ctx, "No text was provided!")
            return
                     
        presences = {
            "streaming": discord.Streaming(
                name=text,
                # Carrying the legacy of a great meme.
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                game="League of Legends",
                platform="YouTube"
            ),
            "playing": discord.Game(
                name=text
            ),
            "listening": discord.Activity(
                name=text,
                type=discord.ActivityType.listening
            ),
            "watching": discord.Activity(
                name=text,
                type=discord.ActivityType.watching
            ),
        }
        
        new_presence = presences.get(status)
        if new_presence is None:
            await Logger.CTX_ERROR(ctx, 
                                   "Failed to change presence! Remember to include a valid status. List of statuses: streaming, playing, listening, and watching.")
            return
        
        await self.bot.change_presence(activity=new_presence)
        await Logger.CTX_SUCCESS(ctx, f"Changed {status} status text to `{text}`")
      
    # Source: https://stackoverflow.com/questions/68188317/how-to-add-disable-command-in-discord-py
    @commands.command(name="cmd")
    @commands.is_owner()
    async def command(self, ctx: commands.Context, new_state: bool, cmd_name: str = None):
        """ 
        Enables or disables a bot command. This takes into account the state of
        the commands at the time this command is provoked.
        """
        if cmd_name is None:
            await Logger.CTX_ERROR(ctx, "You forgot to put down the name of the command.") 
            return
        cmd = self.bot.get_command(cmd_name)
        if not cmd:
            await Logger.CTX_ERROR(ctx, "No valid command name found.")
            return
        if new_state is True:
            if cmd.enabled:
                await Logger.CTX_ERROR(ctx, f"`{cmd_name}` is already turned on!")
                return
            cmd.update(enabled=True)
            await Logger.CTX_ERROR(ctx, f"Successfully enabled command: `{cmd_name}`")
        if new_state is False:
            if not cmd.enabled:
                await Logger.CTX_ERROR(ctx, f"`{cmd_name}` is already turned off!")
                return
            cmd.update(enabled=False)
            await Logger.CTX_ERROR(ctx, f"Successfully disabled command: `{cmd_name}`")

    async def _upload_to_cloud(self, session: aiohttp.ClientSession, url: str, dst_blob_name: str) -> bool:
        """ Helper function with uploading a file to the cloud """
        async with session.get(url) as response:
            if response.status != 200:
                Logger.ERROR("Response status did not return 200. Something went wrong...")
                return False
            content_type = response.headers.get('content-type')
            contents = await response.content.read()
            self.assets_storage.upload_from_memory(contents, dst_blob_name, content_type)
        return True

    @commands.command(name="upload")
    @commands.has_any_role(ADMIN_ROLE)
    async def upload_file(self, ctx: commands.Context):
        """
        Uploads a file to the Assets Storage. For now, it only supports one file at a time
    
        Source for assistance with this command:
        https://stackoverflow.com/questions/59181208/discord-py-bot-take-file-as-argument-to-command
        """
        attachments = ctx.message.attachments
        if len(attachments) == 0:
            await Logger.CTX_ERROR(ctx, "File is not there. What happened?")
            return
        async with HTTPClient(loop=self.bot.loop, name=Helper.get_func_name()) as session:
            for attachment in attachments:
                attachment_name = attachment.filename
                is_valid_filename = self.assets_storage.validate_filename(attachment_name)
                if not is_valid_filename:
                    await Logger.CTX_ERROR(ctx, "Filename is not valid. Try again.")
                    return
                is_uploaded = await self._upload_to_cloud(session, attachment.url, attachment_name)
                if not is_uploaded:
                    await Logger.CTX_ERROR(ctx, f"Something went wrong with uploading {attachment_name}! Aw man.")
                    return
                Logger.DEBUG(f"Uploaded {attachment_name}")
        await Logger.CTX_SUCCESS(ctx, "Uploaded all attachments to cloud!")

    # async def delete_file(self, ctx):
    #     pass
    
    # @commands.command(name="rename")
    # @commands.has_any_role(ADMIN_ROLE)
    # async def rename_file(self, ctx):
    #     pass


async def setup(bot: CustomBot):
    await bot.add_cog(Admin(bot))

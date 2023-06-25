import asyncio

import discord
from discord.ext import commands, tasks
from discord.ext.commands import DefaultHelpCommand

from config import (BOT_SETTINGS_PATH, GREETING_CLIP_PATH, GREETING_ON,
                    GREETING_USER_IDS, GUILD, MEMBER_JOINS_MSG, STATUS_MSG,
                    TOKEN)
from log import Logger

from .managers.voice_manager import VoiceManager
from .subsystems.sys_assets_storage import AssetsStorage
from .subsystems.sys_firebase import Database
from .utils.helper import Helper


class CustomBot(commands.Bot):
    """ The heart of the project. """

    def __init__(self, p_description: str, database: Database,
                 assets_storage: AssetsStorage) -> None:
        """ Create Bot instance """
        super().__init__(
            command_prefix=self.get_cmd_prefix,
            intents=discord.Intents.all(),
            description=p_description,
            help_command=DefaultHelpCommand()
        )

        self.database = database
        self.assets_storage = assets_storage
        self.voice_manager = VoiceManager()

    async def on_ready(self) -> None:
        """ 
        Called when bot is done preparing data received from Discord. 
        May want to read more into this: https://discordpy.readthedocs.io/en/stable/api.html#discord.on_ready
        """
        guild = discord.utils.get(self.guilds, name=GUILD)
        members = '\n - '.join([member.name + ' (id: ' +
                               str(member.id) + ')' for member in guild.members])

        Logger.INFO(
            f'{self.user} is connected to the following server / guild:')
        Logger.INFO(f'{guild.name} (id: {guild.id})')
        Logger.INFO(f'Server Members:\n - {members}')

    @tasks.loop(count=1)
    async def _wait_until_ready(self):
        """ 
        Run any events once after the first on_ready() event. 
        Solution: https://stackoverflow.com/questions/70100227/why-is-my-discord-bot-repeating-the-on-ready-function-endlessly
        """
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Game(name=f"{STATUS_MSG} || >help"))

    def run_bot(self) -> None:
        """ 
        Starts and runs the bot without worrying about
        event loop 
        """
        self._wait_until_ready.start()
        # Will be using project's logger over discord.py's
        self.run(TOKEN, log_handler=None)

    async def start_bot(self) -> None:
        """ 
        Only run this function to start the bot if 
        there is need for control over event loop 
        """
        self._wait_until_ready.start()
        await self.start(TOKEN)

    async def close_bot(self) -> None:
        """ Closes the bot """
        await self.close()

    async def on_message(self, message: discord.Message):
        """ Responds with a friendly message if a user mentions the bot. """
        for x in message.mentions:
            if x == self.user:
                await message.channel.send("What?")
        await self.process_commands(message)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        """ 
        The bot will greet these two specific users down below whenever they
        join a VC in a server. :D 
        """
        # TODO: Maybe store the constants below in the database and rewrite
        # this system to include anyone, rather than specific people. Then, maybe
        # play certain audio clips for certain people. Moreover, have this feature
        # have option to turn on or off

        if not GREETING_ON or not GREETING_CLIP_PATH:
            Logger.DEBUG("Not greeting anyone that joined a voice channel!")
            return

        try:
            channel = member.voice.channel
        except (AttributeError, UnboundLocalError) as error:
            # Don't do anything once encountering these errors; only
            # log them in case anything else happens
            Logger.DEBUG(
                f"Caught channel error in on_voice_state_update: {error}")
            pass

        # Check if they previously went into any other channel. This allows the bot to
        # greet only once after joining a voice channel. If they choose to join another voice
        # channel in the server, the bot will not follow them around.
        if before.channel is None and after.channel is not None:
            if str(member.id) in GREETING_USER_IDS:
                await asyncio.sleep(0.5)

                greeting_audio_name = Helper.get_name(GREETING_CLIP_PATH)
                greeting_audio_file = self.assets_storage.get_audio_file(
                    greeting_audio_name)
                if not greeting_audio_file:
                    Logger.ERROR(f"Cannot play file `{greeting_audio_name}`!")
                    return

                voice = discord.utils.get(self.voice_clients)
                await self.voice_manager.join_channel_and_play_clip(
                    voice, channel, self.assets_storage.audio_file_path)
                self.assets_storage.remove_audio_file()

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """ Set custom error messages for each type of error. """
        author = ctx.author.mention

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"{author}: Sorry, you can't use this command. :)")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"{author}: Wait {error.retry_after:.1f} seconds before using the command again!")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{author}: Missing argument! That means you forgot to put one or more inputs after typing the command name!")

        # NOTE: discord.InvalidArgument does not work in discord.py v2.0.0+. Instead, it is replaced
        # with TypeError and ValueError.
        # elif isinstance(error, discord.InvalidArgument):
        #     Logger.CTX_ERROR(ctx, "Invalid argument! Check your input(s), something is wrong with them.")

        elif isinstance(error, TypeError):
            await Logger.CTX_ERROR(ctx, "TypeError! Check your input(s), something is wrong with them.")

        elif isinstance(error, ValueError):
            await Logger.CTX_ERROR(ctx, "ValueError! Check your input(s), something is wrong with them.")

        elif isinstance(error, discord.HTTPException):
            await Logger.CTX_ERROR(ctx, "HTTP Exception! Here's the full output: ")
            await Logger.CTX_ERROR(ctx, error)

        elif isinstance(error, TimeoutError):
            await ctx.send(f"{author}: Oops! Timeout error! Try again!")

        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(f"{author}: You added too many things after the command!")

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"{author}: I need permission before I could do this!")

        elif isinstance(error, commands.NotOwner):
            await ctx.send(f"{author}: Sorry, you have to be the creator of this bot in order to use this command.")

        elif isinstance(error, commands.MissingRole):
            await ctx.send(f"{author}: Sorry, you don't have the role for this command. Haha silver!")

        elif isinstance(error, commands.errors.CommandNotFound):
            await ctx.send(f"{author}: I can't find any command with that name.")

        elif isinstance(error, commands.errors.CheckFailure):
            pass

        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"{author}: There's an error with your input! Try again!")

        else:
            await ctx.send(error)

        Logger.ERROR(error)

    async def on_member_join(member: discord.Member) -> None:
        """ Send a welcoming message to anyone who joins the server """
        channel = member.guild.text_channels[0]
        await channel.send(f"{member.mention}: {MEMBER_JOINS_MSG}")

    async def get_cmd_prefix(self, bot: commands.Bot, message: discord.Message) -> str:
        """
        A function is needed with Bot and discord.Message as parameters for dynamic command
        prefixes. Read the first paragraph in the provided link below:
        https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.command_prefix

        If command prefix is not available in the database, the function will create one and add
        it into the database.
        """
        try:
            data = self.database.read(BOT_SETTINGS_PATH)
            for key in data:
                prefix = data[key]['cmd_prefix']
            Logger.DEBUG(f"Successfully retrieved command prefix: {prefix}")
            return prefix
        except Exception as e:
            func_name = Helper.get_func_name()
            Logger.DEBUG(f"Catching error in {func_name}: {e}")
            default_prefix = '>'
            Logger.DEBUG("No command prefixes found!")
            Logger.DEBUG(f"Creating default command prefix: {default_prefix}")
            await self.create_cmd_prefix(BOT_SETTINGS_PATH, default_prefix)
            return default_prefix

    async def create_cmd_prefix(self, path: str, cmd_prefix: str = '>'):
        """ Create command prefix if not available. """
        try:
            self.database.add(path, {
                'cmd_prefix': cmd_prefix
            })
            Logger.DEBUG(f"Added {cmd_prefix} to the database!")
        except Exception as e:
            Logger.CRITICAL("Could not create command prefix!")
            Logger.CRITICAL(str(e))

import os

from discord.ext import commands, tasks

from config import ADMIN_ROLE, STAFF_ROLE, TWITCH_USERS_PATH
from log import Logger

from ..bot import CustomBot
from ..subsystems.sys_twitch import TwitchNotification


class Twitch(commands.Cog):
    """ Commands that deal with built-in Twitch notifications. """

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.twitch = TwitchNotification(database=self.bot.database)
        self.check_if_streamers_online.start()

    @commands.command(name='add', aliases=['set', 'insert', 'ins', 'push'],
                      help='Adds a Twitch profile to the database.')
    @commands.has_any_role(ADMIN_ROLE, STAFF_ROLE)
    async def set_twitch_user(self, ctx: commands.Context, twitch_name: str) -> None:
        """ 
        Add Twitch user specified by the Discord user to the database.

        TODO: Refactor the logic if possible (and for other functions too), 
        starting with custom ctx.send messages for error logging and other purposes
        """
        author = ctx.author.mention
        data = self.twitch.get_data_from_db(TWITCH_USERS_PATH)
        twitch_id = self.twitch.get_twitch_id(twitch_name)

        if not twitch_id:
            await ctx.send(f"{author}: Cannot add `{twitch_name}` to the database. Username is invalid.")
            return

        if not data:
            await self.twitch.add_twitch_user(twitch_name, twitch_id, TWITCH_USERS_PATH)
            await ctx.send(f"{author}: Added `{twitch_name}` to the database!")
        else:
            users = [data[key]['user'] for key in data]
            if twitch_name not in users:
                await self.twitch.add_twitch_user(twitch_name, twitch_id, TWITCH_USERS_PATH)
                await ctx.send(f"{author}: Added `{twitch_name}` to the database!")
            else:
                await ctx.send(f"{author}: Cannot add `{twitch_name}` to the database. Username is already in the database.")

    @commands.command(name='update', help='Updates a Twitch profile on the database.')
    @commands.has_any_role(ADMIN_ROLE, STAFF_ROLE)
    async def update_twitch_user(
            self, ctx: commands.Context, old_twitch_name: str, new_twitch_name: str) -> None:
        """ Updates a Twitch profile on the database """
        author = ctx.author.mention
        data = self.twitch.get_data_from_db(TWITCH_USERS_PATH)

        if not data:
            await ctx.send(f"{author}: Database is empty. Have you tried adding some Twitch users first?")

        for key in data:
            # If the old twitch name matches the value in the database, update it with
            # new twitch name
            user = data[key]['user']

            if new_twitch_name == user:
                await ctx.send(f"{author}: `{new_twitch_name}` already exists in the database!")
                return

            elif old_twitch_name == user:
                if self.twitch.get_twitch_id(new_twitch_name) is not None:
                    # Ensure that the path points to the user key
                    await self.twitch.update_twitch_user(old_twitch_name, new_twitch_name, TWITCH_USERS_PATH+f'/{key}')
                    await ctx.send(f"{author}: Updated `{old_twitch_name}` to `{new_twitch_name}` on the database!")
                    return
                else:
                    await ctx.send(f"{author}: `{new_twitch_name}` is not a valid name.")
                    return

        await ctx.send(f"{author}: Could not find `{old_twitch_name}`!")

    @commands.command(name='delete', aliases=['del', 'remove', 'rm', 'pop'],
                      help='Delete your Twitch profile from the live notifs list.')
    @commands.has_any_role(ADMIN_ROLE, STAFF_ROLE)
    async def delete_twitch_user(self, ctx: commands.Context, twitch_name: str) -> None:
        """ Deletes the key of the specified Twitch user """
        author = ctx.author.mention
        data = self.twitch.get_data_from_db(TWITCH_USERS_PATH)
        for key in data:
            if twitch_name == data[key]['user']:
                await self.twitch.delete_twitch_user(key=key, twitch_user=twitch_name, path=TWITCH_USERS_PATH)
                await ctx.send(f"{author}: Deleted `{twitch_name}` from the database!")
                return
        await ctx.send(f"{author}: Can't find `{twitch_name}`!")

    @commands.command(name='get', aliases=['get_users', 'getUsers'], help='Gets all Twitch users in the database.')
    async def get_twitch_users(self, ctx: commands.Context) -> None:
        """ Gets all Twitch users listed in the database  """
        users_list = ''
        data = self.twitch.get_data_from_db(TWITCH_USERS_PATH)
        # Iterate through the data and add every value of 'user' to this
        # amazing string
        for index, key in enumerate(data):
            users_list += f"{index+1}: {data[key]['user']}\n"
        await ctx.send(f"{ctx.author.mention}: List of Twitch users in the database: ")
        await ctx.send(f"```{users_list}```")

    @tasks.loop(minutes=2.5)
    async def check_if_streamers_online(self) -> None:
        try:
            channel = self.bot.get_channel(int(
                os.getenv('TWITCH_NOTIFICATIONS_CHANNEL_ID')))
            streamers = self.bot.database.read('/twitch_users')
            for streamer in streamers:
                streamer_info = streamers[streamer]
                user, user_id = streamer_info['user'], streamer_info['user_id']
                notif_msg = f":red_circle: **LIVE**\n`{user}` is now streaming on Twitch!\nhttps://www.twitch.tv/{user}"
                # Check if they're online or not. If they are, send the notification message to a provided
                # webhook
                status = await self.twitch.check_twitch_user_status(user_id)
                # messages = await channel.history(limit=10).flatten()
                messages = [message async for message in channel.history(limit=10)]
                if status is True:
                    # Check if the messages have already been sent to the channel
                    # Logger.DEBUG(f"messages: {messages}")
                    messages = [msg.content for msg in messages]
                    if not (any(notif_msg in msg for msg in messages)):
                        # Send message to webhook if it exists
                        Logger.DEBUG(
                            f"{str(user)} started streaming. Sending to channel now.")
                        await channel.send(notif_msg)
                    else:
                        Logger.DEBUG(
                            f"notif message about {str(user)} already sent!")
                else:
                    # If offline, clean the channel.
                    for message in messages:
                        if notif_msg == message.content:
                            Logger.DEBUG(
                                f'Deleting notification for: {str(user)}')
                            await message.delete()
        except Exception as e:
            Logger.ERROR(f"Error in Live Notifs Loop: {str(e)}")

    def cog_unload(self):
        """ Cancel the task when unloading this cog """
        self.check_if_streamers_online.cancel()

    @check_if_streamers_online.before_loop
    async def before_check_if_streamers_online(self):
        """ Wait for bot to be ready before starting the task """
        await self.bot.wait_until_ready()


async def setup(bot: CustomBot):
    await bot.add_cog(Twitch(bot))

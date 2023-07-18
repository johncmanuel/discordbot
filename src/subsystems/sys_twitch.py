import os

from twitchAPI.twitch import Twitch

from log import Logger

from .sys_firebase import Database


class TwitchNotification():
    """ 
    A Twitch Notification Subsystem that utilizes Google's Realtime Database to keep track of
    Twitch streamers whenever they go live. Discord admins can keep track of streamers they wish to
    know when they go live. 
    """

    def __init__(self, database: Database) -> None:
        self.twitch = Twitch(os.getenv('TWITCH_CLIENT_ID'),
                             os.getenv('TWITCH_CLIENT_SECRET'))
        self.twitch.authenticate_app([])
        self.database = database

    def _get_twitch_stream(self, user_id: str) -> dict:
        """ Get data about any active streams """
        return self.twitch.get_streams(user_id=user_id)

    def _get_status_of_stream(self, stream) -> str:
        """ Get the status of the streamer """
        return stream['data'][0]['type']

    def _get_users(self, users) -> dict:
        """ Get data about user(s) on Twitch """
        return self.twitch.get_users(logins=users)

    async def check_twitch_user_status(self, user_id) -> bool:
        """ Get status of the twitch user's stream """
        try:
            user_stream = self._get_twitch_stream(user_id)
            return True if self._get_status_of_stream(user_stream) == 'live' else False
        except IndexError:
            return False

    def get_twitch_id(self, user) -> str:
        """ Get numerical id of the user """
        try:
            twitch_id = str(self._get_users(user)['data'][0]['id'])
            Logger.DEBUG(twitch_id)
            return twitch_id
        except IndexError:
            return None

    async def add_twitch_user(self, twitch_user: str, twitch_id, path: str) -> None:
        """ Adds Twitch user to the database """
        try:
            self.database.add(
                path=path,
                data={
                    "user": twitch_user,
                    "user_id": twitch_id
                }
            )
            Logger.DEBUG(f"Added {twitch_user} (ID: {twitch_id}) to database!")
        except Exception as e:
            Logger.CRITICAL(
                f"Could not add {twitch_user} (ID: {twitch_id}) to database!")
            Logger.CRITICAL(e)

    async def update_twitch_user(self, old_twitch_user: str, new_twitch_user: str, path: str) -> None:
        """ Updates Twitch user on the database """
        try:
            self.database.update(
                path=path,
                data={
                    "user": new_twitch_user,
                    "user_id": self.get_twitch_id(new_twitch_user)
                }
            )
            Logger.DEBUG(f"Updated {old_twitch_user} to {new_twitch_user}!")
        except Exception as e:
            Logger.CRITICAL(f"Could not update {old_twitch_user}")
            Logger.CRITICAL(e)

    async def delete_twitch_user(self, twitch_user: str, key, path: str) -> None:
        """ Deletes the key of the Twitch user on the database """
        try:
            self.database.delete(path=path, key=key)
            Logger.DEBUG(f"Deleted {twitch_user}!")
        except Exception as e:
            Logger.CRITICAL(f"Could not delete {twitch_user}")
            Logger.CRITICAL(e)

    def get_data_from_db(self, path: str):
        """ Get data from database """
        return self.database.read(path)

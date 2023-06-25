# from utils.custom_cache import CustomCache
from firebase_admin import db

from log import Logger


class Database():
    """ 
    Database Subsystem that accesses the bot's cloud database 
    See below link for list of data types supported for this DB:
    https://firebase.google.com/docs/firestore/manage-data/data-types
    """

    def __init__(self) -> None:
        """ Set up Firebase Realtime Database """
        # Set up cache
        # self._cache = CustomCache()
        pass

    def _get_ref(self, path: str) -> db.reference:
        """ Get database reference. """
        return db.reference(path)

    def _push_update(self, ref: db.reference, data: dict) -> None:
        """ 
        Push any new updates to the database, which is basically
        another way of adding new data.
        """
        ref.push().update(data)

    def _update(self, ref: db.reference, data: dict) -> None:
        """ Update any existing data from the database """
        ref.update(data)

    def _remove(self, ref: db.reference, key) -> None:
        """ Remove specified data given a key from the database """
        ref.child(key).delete()

    def _get_data(self, ref: db.reference) -> dict:
        """ Retrieve any specified data from the database """
        return ref.get()

    def get_key_value_pair(self, data: dict, target: dict) -> list:
        """ 
        Searches for a specific key value pair in a path, given
        a target key and value, and returns the pair and the
        unique key associated with it. If it doesn't exist, 
        return None. 
        """
        for key in data:
            result = data[key]
            if result == target:
                return [result, key]
        return None

    # @property
    # def cache(self):
    #     return self._cache

    def add(self, path: str, data: dict) -> None:
        """ Add data at a specific path in the database """
        Logger.DEBUG(f"Data to be added: {data}")
        Logger.DEBUG(f"Adding data at: {path}")
        # if data not in self._cache:
        #     cache_key = ()
        #     self._cache[cache_key] = data
        self._push_update(ref=self._get_ref(path), data=data)

    def update(self, path: str, data: dict) -> None:
        """ Update data at a specific path in the database """
        Logger.DEBUG(f"New data that will update old: {data}")
        Logger.DEBUG(f"Updating data at: {path}")
        self._update(ref=self._get_ref(path), data=data)

    def delete(self, path: str, key) -> None:
        """ Remove data from a specific path in the database """
        Logger.DEBUG(f"Key of the data that will be removed: {key}")
        Logger.DEBUG(f"Deleting data from: {path}")
        self._remove(ref=self._get_ref(path), key=key)

    # @CustomCache()
    def read(self, path: str) -> dict:
        """ Get data from a specific path in the database """
        Logger.DEBUG(f"Reading data from: {path}")
        data = self._get_data(ref=self._get_ref(path))
        # if data not in self.cache:
        #     self.cache.add()
        return data

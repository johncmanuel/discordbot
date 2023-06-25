from asyncio import AbstractEventLoop

import aiohttp

from log import Logger


class HTTPClient():
    """ 
    Class wrapper around aiohttp's ClientSession 
    for handling asynchronous HTTP requests with aiohttp. 
    """

    def __init__(self, loop: AbstractEventLoop, status: bool = True,
                 name: str = "Unnamed Session", **kwargs) -> None:
        self.session = aiohttp.ClientSession(
            loop=loop, raise_for_status=status, **kwargs)
        self.session_name = name
        # In case the session names are the same, keep track of the ID of
        # the session
        self.session_id = id(self.session)

    async def close(self):
        Logger.DEBUG(
            f"Ending session: [{self.session_name} {self.session_id}]")
        await self.session.close()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def __aenter__(self):
        Logger.DEBUG(
            f"Starting session: [{self.session_name} {self.session_id}]")
        return self.session

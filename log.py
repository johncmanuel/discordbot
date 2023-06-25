import logging
from enum import Enum

from discord.ext.commands import Context

from config import BOT_ENV


class _Color(Enum):
    """ 
    Collection of constants that store text colors in 
    ANSI escape sequence form.
    Read more here: https://stackoverflow.com/a/33206814

    Enum is needed due to its various benefits 
    Read more here: https://stackoverflow.com/a/37601645
    """
    RED = '\033[91m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\x1b[38;20m'

    # Resets the color persistence when used. Very useful
    # for ending any printed colored strings
    RESET = '\033[0m'


class _ColoredFormatter(logging.Formatter):
    """ 
    Colored version for logger's formatter, which "specifies the layout of log records
    in the final output." (https://docs.python.org/3/library/logging.html)
    """

    COLOR_CODE = {
        'DEBUG': _Color.GREY.value,
        'INFO': _Color.GREEN.value,
        'WARNING': _Color.YELLOW.value,
        'ERROR': _Color.RED.value,
        'CRITICAL': _Color.RED.value
    }
    RESET_CODE = _Color.RESET.value

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color_code = self.COLOR_CODE.get(record.levelname, '')
        reset_code = self.RESET_CODE
        return f'{color_code}{message}{reset_code}'


class _CustomLogger():
    """ Custom logger that includes color schemes """

    def __init__(self, name: str = __name__):
        LOG_LVL = logging.DEBUG if BOT_ENV == 'DEV' else logging.CRITICAL
        self.name = name

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LVL)
        self.logger.handlers.clear()
        format = "[%(asctime)s] %(levelname)s: %(message)s"

        # Create handler
        handler = logging.StreamHandler()
        handler.setLevel(LOG_LVL)
        handler.setFormatter(_ColoredFormatter(format))

        self.logger.addHandler(handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


class Logger():
    """ Interface class that allows logging for the application """

    _logger = _CustomLogger()

    @classmethod
    def DEBUG(cls, message):
        cls._logger.debug(message)

    @classmethod
    def INFO(cls, message):
        cls._logger.info(message)

    @classmethod
    def WARNING(cls, message):
        cls._logger.warning(message)

    @classmethod
    def ERROR(cls, message):
        cls._logger.error(message)

    @classmethod
    def CRITICAL(cls, message):
        cls._logger.critical(message)

    """ Below are logging functions for messaging the users in Discord directly """

    @staticmethod
    async def CTX_ERROR(ctx: Context, message: str) -> None:
        """ Send error messages to the user """
        await ctx.send(f"{ctx.author.mention}: ERROR: {message}")

    @staticmethod
    async def CTX_INFO(ctx: Context, message: str) -> None:
        """ Send informational messages to the user """
        await ctx.send(f"{ctx.author.mention}: {message}")

    @staticmethod
    async def CTX_SUCCESS(ctx: Context, message: str) -> None:
        """ Send successful messages to the user """
        await ctx.send(f"{ctx.author.mention}: SUCCESS: {message}")

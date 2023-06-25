import os

from dotenv import load_dotenv
from pytz import timezone

from src.config_parser import CustomConfigParser

config = CustomConfigParser("config.ini")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

if not TOKEN or not GUILD:
    raise Exception(
        "TOKEN or GUILD not given, please insert your Discord bot token and/or name of your server, please! ")

# TODO: Make admin role and staff roles modifiable on the database.
# Maybe add them to bot_settings so they can be modified via admin.py?
ADMIN_ROLE = int(config.get_bot_value("admin_role"))
STAFF_ROLE = int(config.get_bot_value("staff_role"))

if not ADMIN_ROLE:
    raise ValueError("ADMIN_ROLE not found, please set it to a valid ID.")
if not STAFF_ROLE:
    STAFF_ROLE = ADMIN_ROLE

BOT_ENV = os.getenv('BOT_ENV')

# WRAPAPI_KEY = os.getenv('WRAPAPI_KEY')

# Default database paths
# TODO: Make them modifiable
BOT_SETTINGS_PATH = config.get_bot_db_value("bot_settings")
TWITCH_USERS_PATH = config.get_bot_db_value("twitch_users")

TIMEZONE_REGION = config.get_bot_value("timezone")

if not TIMEZONE_REGION:
    TIMEZONE_REGION = "US/Pacific"

TIMEZONE = timezone(TIMEZONE_REGION)

PROJ_CACHE_PATH = "./.proj_cache"
DISCORD_COGS_PATH = "./src/cogs"

GREETING_ON = config.get_bot_value("greeting_on")

if not GREETING_ON:
    # If GREETING_ON is None
    GREETING_ON = False
else:
    GREETING_ON = bool(GREETING_ON)

GREETING_CLIP_PATH = config.get_bot_value("greeting_clip_path")

if GREETING_ON and not GREETING_CLIP_PATH:
    raise Exception(
        "GREETING_CLIP_PATH not given, please give a path in your GCS database!")

GREETING_USER_IDS = (config.get_bot_value(
    "greeting_user_ids")).replace(" ", "").split(",")

if GREETING_ON and not GREETING_USER_IDS:
    raise Exception(
        "GREETING_USER_IDs is None, please insert at least one Discord user ID.")

EXCLUDED_COGS = (config.get_bot_value("excluded_cogs")).strip().split(",")

BOT_DESC = config.get_bot_value("description")

if not BOT_DESC:
    BOT_DESC = "My amazing bot"

MEMBER_JOINS_MSG = config.get_bot_value("member_joins_msg!")
STATUS_MSG = config.get_bot_value("status_msg")

if not MEMBER_JOINS_MSG:
    MEMBER_JOINS_MSG = "Hello World!"
if not STATUS_MSG:
    STATUS_MSG = "Welcome!"

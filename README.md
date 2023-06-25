# discordbot

A customizable, dynamic Discord bot written in discord.py with a handful of features, utilizing thirdparty API's (twitch.tv, Riot Games) and databases for storing settings and external media (Google Realtime Database and Cloud Storage, respectively).

## TODO

1. Implement caching system so number of calls made to database decreases. This will also be used for anything that makes expensive calls to external API's
2. Develop an API wrapper (probably around zoro.to) for requesting anime episodes
3. Make admin role and staff roles modifiable on the database. Maybe add them to bot_settings?
4. Create a root node in the database that stores all the information needed for a particular server. (ex. Server 1 will have their own command prefixes, twitch streamers to keep track of, etc. Server 2's information will differ from Server 1)
5. Solve any TODOs or bugs in the codebase
6. Add more unit tests whenever possible
7. Add config file to modify settings such as name of bot, description, what font to use for meme generators, etc.
8. Create music functionality for the bot
9. Implement birthday notification feature to keep track of user's birthdays and notify server(?) that it is their birthday.
10. Implement a CI/CD system.

## Preparations

Requires Python 3.8.8.

> NOTE: Bot was tested on 3.11.\*; however, packages used for the bot were not compatible.

Fork this repo and clone it to your computer, then follow the steps below to set up API's and other dependencies. Though, if you wish to contribute to this project, clone this repo.

1. [Set up your Discord bot settings](https://discord.com/developers/docs/intro)

2. [Get an API key from Riot Games](https://developer.riotgames.com/)

3. [Get Twitch API Key and Secrets](https://dev.twitch.tv/docs/api/)

4. [Set up a Google Firebase Project](https://firebase.google.com)

    - Then, download your secrets (in JSON format) from "Service accounts" (found in Project settings) and store them somewhere secure. From the file, keep note of the following information as you'll need them later:
        - project_id
        - client_email
        - private_key
    - Afterwards, create a Firebase Realtime Database.
        - Keep track of the provided URL; you'll need it later.
    - Then, create a Firebase Storage.
        - Keep track of the name of your storage in the provided URL: `gs://<your storage name>.appspot.com`; you'll need it too.

5. [Install FFMPEG](https://www.ffmpeg.org/download.html) and add its `bin` folder to your PATH environment variable.

<!-- Finally, sign up for an API key at Wrap API:

Wrap API: https://wrapapi.com/ -->

## Set up Local Development Environment

Create an .env file and set up the following variables:

```
DISCORD_TOKEN=<your token>
DISCORD_GUILD=<your guild>

TWITCH_CLIENT_ID=<your client ID>
TWITCH_CLIENT_SECRET=<your client secret>
TWITCH_NOTIFICATIONS_CHANNEL_ID=<the channel ID you want to send Twitch notifications to>

# The following information can be found in your secrets file downloaded from earlier
FIREBASE_DB_URL=<your link to database>
FIREBASE_PROJECT_ID=<your name of the project>
FIREBASE_PRIVATE_KEY=<your private key>
FIREBASE_CLIENT_EMAIL=<your client email with Firebase>

FIREBASE_STORAGE_NAME=<name of your storage>

ADMIN_ROLE=<the ID of an admin role, if applicable>
STAFF_ROLE=<the ID of a staff role, if applicable>

BOT_ENV=<DEV for development environment; PROD for production environment>

RIOT_API_KEY=<your Riot Games API key>
```

Then, install [pipenv](https://github.com/pypa/pipenv), a Python virtualenv management tool. You may want to refer to [the installation section](https://github.com/pypa/pipenv#installation) and install accordingly to your setup.

Use the following commands to set up a virtual environment:

```powershell
pipenv --python 3.8.8
pipenv install --dev
pipenv lock
```

Then, customize config.ini to fit your needs. Omit or delete the options that you don't need.

Finally, run the application:

```powershell
# Windows Powershell
pipenv run python ./app.py
```

```bash
# Bash, Windows Command Line, etc.
pipenv run python app.py
```

To see all commands for the bot, type `>help`

## Testing the Bot and other components

Run the following to install the project as a local, editable package:

```bash
pipenv install --dev -e .
```

This will allow `/tests` to import modules from `/src`.

Then, to run all tests in `/tests`:

```bash
pipenv run pytest
```

Alternatively, you can individually test each file in `/tests`:

```bash
# Windows Powershell
pipenv run pytest
```

```powershell
# Windows Powershell
pipenv run pytest .\tests\test_<name of test file>.py
```

```bash
# Bash, Windows Command Line, etc.
pipenv run pytest tests\test_<name of test file>.py
```

## Deploying & Hosting Bot

For deploying the bot, I use [Heroku](https://www.heroku.com/). I use Heroku over other platforms due to the premium developer experience it offers. You do not have to use Heroku to deploy the bot--you may use other cloud platform services if you wish.

import asyncio

import discord

from log import Logger

from ..utils.helper import Helper


class VoiceManager:
    """ 
    Manages voice channel functions and logic. Many aspects of the bot will 
    utilize the voice channel, so it's best to add any functions here 
    """

    def __init__(self) -> None:
        pass

    # def is_connected(ctx: commands.Context):
    #     voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    #     return voice_client and voice_client.is_connected()

    def _play_clip(self, src, vc: discord.VoiceClient, volume: int):
        """ Plays a clip, given a path and a voice channel connection. """
        Logger.DEBUG(f"Now playing clip {src}")
        vc.play(
            discord.FFmpegPCMAudio(source=src),
            after=lambda e: Logger.DEBUG(f"Finished playing clip: {src}"))
        vc.source = discord.PCMVolumeTransformer(vc.source)
        vc.source.volume = volume

    async def join_channel_and_play_clip(self, voice: discord.VoiceClient,
                                         channel: discord.VoiceChannel,
                                         src: str, audio_volume: int = 1.0):
        """ Joins the channel and plays a clip """
        channel_name = str(channel)
        additional_seconds = 0.5
        Logger.DEBUG(f"Now attempting to join {channel_name}")

        if voice is not None:
            Logger.DEBUG(f"Bot already in `{channel_name}`")
            return

        vc = await channel.connect()
        self._play_clip(src, vc, audio_volume)
        Logger.DEBUG(f"Joined `{channel_name}`")

        # Stay in the voice channel for the duration of the clip plus a
        # few more seconds
        audio_length = Helper.get_length_of_audio_src(src)
        await asyncio.sleep(audio_length + additional_seconds)
        await vc.disconnect()

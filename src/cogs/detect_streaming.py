import logging
import discord
from discord.ext import commands
from config import D2K_SERVER_ID

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class StreamNotifier(commands.Cog):
    """
    Notifies the server when a user starts or stops streaming in a voice channel.
    """

    def __init__(self, bot):
        self.bot = bot
        self.active_streams = {}  # Tracks active streams {member_id: voice_channel_id}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Triggered when a member's voice state changes.
        This checks if a member starts or stops streaming.
        """

        # Ensure we only process events from the intended guild
        if member.guild.id != D2K_SERVER_ID:
            return

        # Get the system channel
        system_channel = member.guild.system_channel
        if system_channel is None:
            return  # No system channel available

        # Get the voice channel
        voice_channel = after.channel if after.channel else before.channel
        channel_link = f"https://discord.com/channels/{member.guild.id}/{voice_channel.id}" if voice_channel else "Unknown Voice Channel"

        try:
            # Detect streaming start
            if not before.self_stream and after.self_stream:
                self.active_streams[member.id] = voice_channel.id  # Store active stream
                message = f'**{member.display_name}** has started a live stream in {channel_link}! <:D2K_Worm:1189389809878323380>'
                logger.info(f"Stream started by {member.display_name} in {voice_channel.name}")
                await system_channel.send(message)

            # Detect streaming stop (either they stopped streaming or left the channel)
            elif (before.self_stream and not after.self_stream) or (before.self_stream and after.channel is None):
                if member.id in self.active_streams:
                    del self.active_streams[member.id]  # Remove from active streams
                    message = f'**{member.display_name}** has stopped streaming in {channel_link}.'
                    logger.info(
                        f"Stream stopped by {member.display_name} in {voice_channel.name if voice_channel else 'Unknown'}")
                    await system_channel.send(message)

        except discord.errors.DiscordServerError as e:
            logger.warning(
                f"Discord server error while sending message in {system_channel.name} (ID: {system_channel.id}): {e}")
        except discord.errors.HTTPException as e:
            logger.warning(f"HTTP error while sending message in {system_channel.name} (ID: {system_channel.id}): {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error while sending message in {system_channel.name} (ID: {system_channel.id}): {e}")


async def setup(bot):
    await bot.add_cog(StreamNotifier(bot), guild=guild)

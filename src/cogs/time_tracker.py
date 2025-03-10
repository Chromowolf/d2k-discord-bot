import logging
from discord.ext import commands, tasks
import time
import discord
from config import TIME_CHANNEL_ID, D2K_SERVER_ID

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class TimeTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = TIME_CHANNEL_ID  # Must be int, not string!!!
        self.time_update.start()

    async def send_or_update_embed(self, channel, embed):
        """Send a new message or update the latest bot message and delete older ones.

        Args:
            channel: The channel to send/update messages in
            embed: The embed to send
        """
        # Get all messages from the bot in this channel (limited to a reasonable amount)
        bot_messages = []
        async for message in channel.history(limit=10):
            if message.author.id == self.bot.user.id:
                bot_messages.append(message)

        if not bot_messages:
            # No existing messages, send a new one
            await channel.send(embed=embed)
        else:
            # Update the most recent message
            latest_message = bot_messages[0]  # First message is the most recent
            await latest_message.edit(embed=embed)

            # Delete any older messages from the bot
            if len(bot_messages) > 1:
                for old_message in bot_messages[1:]:
                    await old_message.delete()

    @tasks.loop(seconds=60)
    async def time_update(self):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if channel:
            # Get current Unix timestamp
            current_timestamp = int(time.time())

            # Create an embed for the timestamp
            embed = discord.Embed(
                title="Current Time",
                description=f"<t:{current_timestamp}:F>",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Timestamp: {current_timestamp}")

            await self.send_or_update_embed(channel, embed)
        else:
            logger.error(f"Channel with ID {self.CHANNEL_ID} not found.")

    @time_update.before_loop
    async def before_time_update(self):
        """Wait for the bot to be ready before starting the loop."""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TimeTracker(bot), guild=guild)

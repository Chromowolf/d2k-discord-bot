import logging
import time
import asyncio
import datetime
import discord
from config import TIME_CHANNEL_ID

logger = logging.getLogger(__name__)


class TimeTracker:
    def __init__(self, client):
        self.client = client
        self.task = None

    async def start(self):
        """Start the time update task."""
        if self.task is not None:
            self.task.cancel()

        self.task = self.client.loop.create_task(self.time_update_loop())
        logger.info("Started time update task")

    async def time_update_loop(self):
        """Loop that sends time updates every minute."""
        try:
            # Wait for the bot to be ready before getting the channel
            await self.client.wait_until_ready()

            channel = self.client.get_channel(TIME_CHANNEL_ID)
            if not channel:
                logger.error(f"Could not find channel with ID {TIME_CHANNEL_ID}")
                return

            logger.info(f"Starting time updates in channel: {channel.name}")

            while not self.client.is_closed():
                # Get current Unix timestamp
                current_timestamp = int(time.time())

                # Create an embed for the timestamp
                embed = discord.Embed(
                    title="Current Time",
                    description=f"<t:{current_timestamp}:F>",
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Timestamp: {current_timestamp}")

                await channel.send(embed=embed)

                # Calculate the delay until the next minute
                now = datetime.datetime.now()
                next_minute = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
                delay = (next_minute - now).total_seconds()

                await asyncio.sleep(delay)

        except asyncio.CancelledError:
            logger.info("Time update task was cancelled")
        except Exception as e:
            logger.exception(f"Error in time update loop: {e}")


def setup_time_tracker(client):
    """Set up the time tracker for the client."""
    time_tracker = TimeTracker(client)

    # Start the time tracker when the bot is ready
    original_on_ready = client.on_ready

    async def on_ready_wrapper():
        await original_on_ready()
        await time_tracker.start()

    client.on_ready = on_ready_wrapper

    logger.info("Time tracker registered")

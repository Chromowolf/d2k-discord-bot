import discord
from discord import app_commands
import logging
from config import D2K_SERVER_ID

from cogs.basic_commands import setup_basic_commands
# from cogs.time_tracker import setup_time_tracker

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Register all cogs
        setup_basic_commands(self)
        # setup_time_tracker(self)

        try:
            # Clear global commands first
            # self.tree.clear_commands(guild=None)
            # await self.tree.sync()
            # logger.info("Cleared all global commands")

            # Then sync guild-specific commands
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands to guild {guild.id}.")
            # Log details of each command
            for cmd in synced:
                logger.info(f"  - Command: {cmd.name} (ID: {cmd.id})")
        except Exception as e:
            logger.exception(f"Error syncing commands: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}')
        logger.info('------')


def create_client():
    """Factory function to create and configure a new client."""
    return MyClient()

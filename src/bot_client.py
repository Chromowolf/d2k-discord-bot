import discord
# from discord import app_commands
from discord.ext import commands
import logging
from config import D2K_SERVER_ID

from cogs.basic_commands import setup_basic_commands
from cogs.execuses import setup_excuses
from cogs.time_tracker import setup_time_tracker

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)  # "!" is just a placeholder
        # self.tree = app_commands.CommandTree(self)
        self.time_tracker = None

    async def setup_hook(self):
        # Register all cogs
        setup_basic_commands(self)
        setup_excuses(self)
        setup_time_tracker(self)

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
        # To be wrapped by other cogs
        logger.info(f'Logged in as {self.user}')
        logger.info('------')


def create_client():
    """Factory function to create and configure a new client."""
    return MyClient()

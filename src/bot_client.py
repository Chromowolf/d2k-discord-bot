import discord
from discord import app_commands
import logging
from cogs.basic_commands import setup_basic_commands
# from cogs.time_tracker import setup_time_tracker

logger = logging.getLogger(__name__)


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Register all cogs
        setup_basic_commands(self)
        # setup_time_tracker(self)

        # Sync commands
        await self.tree.sync()
        logger.info(f"Synced commands for {self.user}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}')
        logger.info('------')


def create_client():
    """Factory function to create and configure a new client."""
    return MyClient()

import discord
from discord.ext import commands
import logging
from config import D2K_SERVER_ID

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)  # "!" is just a placeholder
        self.cogs_list = [
            "basic_commands",
            "excuses",
            "time_tracker",
        ]

    async def setup_hook(self):
        # Load all cogs
        for cog in self.cogs_list:
            cog_name = f"cogs.{cog}"
            logger.info(f"Loading extension {cog_name}")
            await self.load_extension(cog_name)

        try:
            # Clear global commands first
            # self.tree.clear_commands(guild=None)
            # await self.tree.sync()
            # logger.info("Cleared all global commands")

            # Then sync guild-specific app_commands
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

import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import D2K_SERVER_ID

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # intents = discord.Intents.all()
        intents.message_content = True

        # Added help_command=None to disable the default "!help" command
        super().__init__(command_prefix="!", intents=intents, help_command=None)  # "!" is just a placeholder
        self.cogs_list = [
            "basic_commands",
            "excuses",
            "ircbot",
            "youtube",
            "detect_streaming",
            "autoreaction",
        ]

    async def setup_hook(self):
        # Load all cogs
        for cog in self.cogs_list:
            cog_name = f"cogs.{cog}"
            logger.info(f"Loading extension {cog_name}")
            await self.load_extension(cog_name)

        # Register global app command error handler
        self.tree.error(self.app_command_error_handler)

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

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # Silently ignore command not found errors (triggered by "!" user messages)
            return
        # Log other errors
        logger.error(f"Command error: {error}")

    # Centralize all the "cog_app_command_error"
    # noinspection PyMethodMayBeStatic
    async def app_command_error_handler(
            self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Global error handler for application commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            response = f"You're on cooldown! Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, app_commands.CheckFailure):
            response = "You don't have permission to use this command!"
        else:
            logger.error(f"App command error: {error}")
            response = "An unknown error occurred."

        # noinspection PyUnresolvedReferences
        if interaction.response.is_done():
            await interaction.followup.send(response, ephemeral=True)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(response, ephemeral=True)


def create_client():
    """Factory function to create and configure a new client."""
    return MyClient()

import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import D2K_SERVER_ID
import os
from utils.command_checks import is_creator

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)
DATA_FOLDER = "data"

class MyClient(commands.Bot):
    def __init__(self):
        # intents = discord.Intents.default()  # Cannot use on_member_join
        intents = discord.Intents.all()
        intents.message_content = True

        # Ensure the data folder exists before loading cogs
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            logger.info(f"Created missing data folder: {DATA_FOLDER}")

        # Added help_command=None to disable the default "!help" command
        super().__init__(command_prefix="!", intents=intents, help_command=None)  # "!" is just a placeholder
        self.cogs_list = [
            "basic_commands",
            "excuses",
            "ircbot",
            "youtube",
            "detect_streaming",
            "autoreaction",
            "ai_chat",
        ]

    async def setup_hook(self):
        # Load all cogs
        for cog in self.cogs_list:
            cog_name = f"cogs.{cog}"
            logger.info(f"Loading extension {cog_name}")
            await self.load_extension(cog_name)  # the app commands in the cogs are auto added

        # Manually add the commands to the command tree
        self.tree.add_command(self.loadext, guild=guild)
        self.tree.add_command(self.unloadext, guild=guild)

        # Register global app command error handler
        self.tree.error(self.app_command_error_handler)
        await self.sync_commands()

    async def sync_commands(self):
        try:
            # Clear global commands first
            self.tree.clear_commands(guild=None)
            self.tree.clear_commands(guild=guild)
            await self.tree.sync()
            logger.info("Cleared all existing commands")

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

    @app_commands.command(name="loadext", description="[Admin only]")
    @app_commands.check(is_creator)
    async def loadext(self, interaction: discord.Interaction, cog: str):
        """Slash command to load a cog dynamically"""
        cog_path = f"cogs.{cog}"
        try:
            try:
                await self.load_extension(cog_path)
                # noinspection PyUnresolvedReferences
                await self.sync_commands()  # Resync commands after modification
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"✅ Successfully loaded `{cog}` cog.", ephemeral=True)
                logger.info(f"Loaded cog: {cog}")
            except ModuleNotFoundError:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"❌ Cog `{cog}` not found! Make sure it exists in `cogs/`.",
                                                        ephemeral=True)
                logger.error(f"Failed to load cog `{cog}`: Module not found.")
            except commands.ExtensionFailed as e:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"❌ Cog `{cog}` exists but failed to load!\nError: {e}",
                                                        ephemeral=True)
                logger.error(f"Failed to load cog `{cog}`: {e}")
            except Exception as e:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"❌ Unexpected error loading `{cog}`: {e}", ephemeral=True)
                logger.exception(f"Unexpected error loading extension `{cog}`: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error when sending error message when loading extension `{cog}`: {e}")

    @app_commands.command(name="unloadext", description="[Admin only]")
    @app_commands.check(is_creator)
    async def unloadext(self, interaction: discord.Interaction, cog: str):
        """Slash command to load a cog dynamically"""
        cog_path = f"cogs.{cog}"
        try:
            # Check if the extension is loaded
            if cog_path not in self.extensions:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(
                    f"❌ The cog `{cog}` is not loaded or does not exist.",
                    ephemeral=True
                )
                logger.warning(f"Attempted to unload non-existent cog: {cog}")
                return

            try:
                await self.unload_extension(cog_path)
                # noinspection PyUnresolvedReferences
                await self.sync_commands()  # Resync commands after modification
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"✅ Successfully unloaded `{cog}` cog.", ephemeral=True)
                logger.info(f"Unloaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to unload cog {cog}: {e}")
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(
                    f"❌ The cog `{cog}` exists but failed to unload. Error: {e}",
                    ephemeral=True
                )
        except Exception as e:
            logger.exception(f"Unexpected error when sending error message when unloading extension `{cog}`: {e}")

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

import logging
import discord
from discord.ext import commands
from discord import app_commands
from config import D2K_SERVER_ID
from utils.command_checks import is_creator

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)


class ExtensionControl(commands.Cog):
    """
    Register all basic commands with the client.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loadext", description="[Admin only]")
    @app_commands.check(is_creator)
    async def loadext(self, interaction: discord.Interaction, ext: str):
        """Slash command to load an extension dynamically"""
        ext_path = f"cogs.{ext}"
        try:
            try:
                await self.bot.load_extension(ext_path)
                # noinspection PyUnresolvedReferences
                await self.bot.sync_commands()  # Resync commands after modification
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"✅ Successfully loaded `{ext}` extension.", ephemeral=True)
                logger.info(f"Loaded extension: {ext}")
            except ModuleNotFoundError:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"❌ Extension `{ext}` not found! Make sure it exists in `cogs/`.",
                                                        ephemeral=True)
                logger.error(f"Failed to load xxtension `{ext}`: Module not found.")
            except commands.ExtensionFailed as e:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"❌ Extension `{ext}` exists but failed to load!\nError: {e}",
                                                        ephemeral=True)
                logger.error(f"Failed to load xxtension `{ext}`: {e}")
            except Exception as e:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"❌ Unexpected error loading `{ext}`: {e}", ephemeral=True)
                logger.exception(f"Unexpected error loading extension `{ext}`: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error when sending error message when loading extension `{ext}`: {e}")

    @app_commands.command(name="unloadext", description="[Admin only]")
    @app_commands.check(is_creator)
    async def unloadext(self, interaction: discord.Interaction, ext: str):
        """Slash command to load an extension dynamically"""
        ext_path = f"cogs.{ext}"
        try:
            # Check if the extension is loaded
            if ext_path not in self.bot.extensions:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(
                    f"❌ The extension `{ext}` is not loaded or does not exist.",
                    ephemeral=True
                )
                logger.warning(f"Attempted to unload non-existent extension: {ext}")
                return

            try:
                await self.bot.unload_extension(ext_path)
                # noinspection PyUnresolvedReferences
                await self.bot.sync_commands()  # Resync commands after modification
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(f"✅ Successfully unloaded `{ext}` extension.", ephemeral=True)
                logger.info(f"Unloaded extension: {ext}")
            except Exception as e:
                logger.error(f"Failed to unload extension {ext}: {e}")
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(
                    f"❌ The extension `{ext}` exists but failed to unload. Error: {e}",
                    ephemeral=True
                )
        except Exception as e:
            logger.exception(f"Unexpected error when sending error message when unloading extension `{ext}`: {e}")

async def setup(bot):
    await bot.add_cog(ExtensionControl(bot), guild=guild)

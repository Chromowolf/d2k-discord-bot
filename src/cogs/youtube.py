import discord
import logging
from config import D2K_SERVER_ID, SEND_MESSAGE_CHANNEL_ID
import json
from discord import app_commands
from discord.ext import commands, tasks
from utils.command_checks import is_creator
from utils.discord_msg import send_a_message_then_delete
import os

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

# File path for storing YouTube channels
# Define the file path inside the 'data' folder
# Make sure the data folder is right in the working dir!!!
DATA_FOLDER = "data"
FILE_PATH = os.path.join(DATA_FOLDER, "youtube_channels.json")

# Function to load data from JSON file
def load_youtube_channels():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Function to save data to JSON file
def save_youtube_channels(data):
    with open(FILE_PATH, "w", encoding="utf-8") as file:
        # noinspection PyTypeChecker
        json.dump(data, file, indent=4)

class YouTubeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube_channels = load_youtube_channels()  # Load channels on startup

        # This is useless, because other bots by default ignore the command sent by any bot account
        # self.invoke_youtube_update_task.start()

    @app_commands.command(name="youtube", description="Displays the YouTube channels of the players.")
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    async def youtube(self, interaction):
        if not self.youtube_channels:
            await interaction.response.send_message("No YouTube channels found.", ephemeral=True)
            return

        youtube_channel_list = [f"[**{name}**]({url})" for name, url in self.youtube_channels.items()]
        embed = discord.Embed(
            title="Players YouTube Channels",
            description="\n".join(youtube_channel_list),
            color=discord.Color.red()
        )
        embed.set_thumbnail(
            url="https://png.pngtree.com/png-clipart/20221018/ourmid/pngtree-youtube-social-media-3d-stereo-png-image_6308427.png"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addytchannel", description="[Admin only] Adds a YouTube channel for a player.")
    @app_commands.check(is_creator)
    async def addytchannel(self, interaction, player_name: str, url: str):
        update_player = player_name in self.youtube_channels  # if already exists, then update, else add
        self.youtube_channels[player_name] = url
        save_youtube_channels(self.youtube_channels)
        if update_player:
            await interaction.response.send_message(f"✅ Updated YouTube channel for **{player_name}**: {url}", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Added YouTube channel for **{player_name}**: {url}", ephemeral=True)

    @app_commands.command(name="removeytchannel", description="[Admin only] Removes a YouTube channel from the list.")
    @app_commands.check(is_creator)
    async def removeytchannel(self, interaction, player_name: str):
        if player_name in self.youtube_channels:
            del self.youtube_channels[player_name]
            save_youtube_channels(self.youtube_channels)
            await interaction.response.send_message(f"✅ Removed YouTube channel for **{player_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Player **{player_name}** not found.", ephemeral=True)

    # Periodically invoke the other bot:
    @tasks.loop(seconds=60)
    async def invoke_youtube_update_task(self):
        await send_a_message_then_delete(self.bot, SEND_MESSAGE_CHANNEL_ID, "!updateyt2000")

    @invoke_youtube_update_task.before_loop
    async def before_invoke_youtube_update_task(self):
        await self.bot.wait_until_ready()
        logger.info("Start invoke_youtube_update task.")

    # handle errors together
    # async def cog_app_command_error(self, interaction, error: app_commands.AppCommandError):
    #     if isinstance(error, app_commands.CommandOnCooldown):
    #         response = f"You're on cooldown! Try again in {error.retry_after:.2f} seconds."
    #     elif isinstance(error, app_commands.CheckFailure):  # Handles permission errors, etc.
    #         response = "You don't have permission to use this command!"
    #     else:
    #         response = "An unknown error occurred."
    #
    #     # noinspection PyUnresolvedReferences
    #     if interaction.response.is_done():
    #         await interaction.followup.send(response, ephemeral=True)
    #     else:
    #         # noinspection PyUnresolvedReferences
    #         await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(YouTubeCog(bot), guild=guild)

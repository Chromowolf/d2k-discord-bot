import discord
import logging
from config import D2K_SERVER_ID
import json
from discord import app_commands
from discord.ext import commands
from utils.command_checks import is_creator
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

    @app_commands.command(name="youtube", description="Displays the YouTube channels of the players.")
    async def youtube(self, interaction):
        if not self.youtube_channels:
            await interaction.response.send_message("No YouTube channels found.", ephemeral=True)
            return

        youtube_channel_list = [f"**{name}**: [link]({url})" for name, url in self.youtube_channels.items()]
        embed = discord.Embed(
            title="Players YouTube Channels",
            description="\n".join(youtube_channel_list),
            color=discord.Color.red()
        )
        embed.set_thumbnail(
            url="https://png.pngtree.com/png-clipart/20221018/ourmid/pngtree-youtube-social-media-3d-stereo-png-image_6308427.png"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addytchannel", description="Adds a YouTube channel for a player.")
    @app_commands.check(is_creator)
    async def addytchannel(self, interaction, player_name: str, url: str):
        self.youtube_channels[player_name] = url
        save_youtube_channels(self.youtube_channels)
        await interaction.response.send_message(f"✅ Added YouTube channel for **{player_name}**.", ephemeral=True)

    @app_commands.command(name="removeytchannel", description="Removes a YouTube channel from the list.")
    @app_commands.check(is_creator)
    async def removeytchannel(self, interaction, player_name: str):
        if player_name in self.youtube_channels:
            del self.youtube_channels[player_name]
            save_youtube_channels(self.youtube_channels)
            await interaction.response.send_message(f"✅ Removed YouTube channel for **{player_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Player **{player_name}** not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(YouTubeCog(bot), guild=guild)

import discord
import logging
from config import D2K_SERVER_ID, VIDEO_CHANNEL_ID, YOUTUBE_API_TOKEN
import json
from discord import app_commands
from discord.ext import commands, tasks
from utils.command_checks import is_creator
# from utils.discord_msg import send_a_message_then_delete
import os
import aiohttp
import re

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

# File path for storing YouTube channels
# Define the file path inside the 'data' folder
# Make sure the data folder is right in the working dir!!!
DATA_FOLDER = "data"
FILE_PATH = os.path.join(DATA_FOLDER, "player_youtube_info.json")

api_url = "https://www.googleapis.com/youtube/v3/"
url_channels = api_url + "channels"
url_playlist = api_url + "playlistItems"

ts_re = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

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


async def get_youtuber_info(custom_handle):
    async with aiohttp.ClientSession() as session:
        async with session.get(url_channels, params={
            "part": "snippet,id,contentDetails",
            "forHandle": custom_handle,  # Use the handle to search for the channel ID
            "key": YOUTUBE_API_TOKEN
        }) as response:
            if response.status != 200:
                logger.error(f"[get_youtuber_info] Error fetching data: {response.status}")
                return None

            channel_data = await response.json()

    if "items" not in channel_data or not channel_data["items"]:
        logger.error(f"[get_youtuber_info] ❌ No channel found for this handle: {custom_handle}")
        return None
    channel_info = channel_data["items"][0]

    playlist_id = channel_info["contentDetails"]["relatedPlaylists"]["uploads"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url_playlist, params={
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 1,
            "key": YOUTUBE_API_TOKEN
        }) as response:
            if response.status != 200:
                logger.error(f"[get_youtuber_info] Error fetching data in: {response.status}")
                return None
            play_list_data = await response.json()
    if "items" not in play_list_data or not play_list_data["items"]:
        logger.error(f"[get_youtuber_info] ❌ No videos found for playlist ID: {playlist_id}")
        return None
    last_upload_datetime = play_list_data["items"][0]["snippet"]["publishedAt"]

    key_info = {
        "channel_name": channel_info["snippet"]["title"],
        "handle": channel_info["snippet"].get("customUrl", "Not available"),  # This is the closest to a username
        "channel_id": channel_info["id"],
        "playlist_id": playlist_id,
        "profile_picture": channel_info["snippet"]["thumbnails"]["default"]["url"],
        "last_upload_datetime": last_upload_datetime,
    }
    return key_info


async def get_latest_videos(playlist_id: str, after_timestamp: str, max_number=5):
    """
    Fetch latest videos from a given playlist ID after the specified timestamp.
    """
    if after_timestamp and not ts_re.match(after_timestamp):
        logger.error("Malformed timestamp!")
        return []

    async with aiohttp.ClientSession() as session:
        async with session.get(url_playlist, params={
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": max_number,
            "key": YOUTUBE_API_TOKEN
        }) as response:
            if response.status != 200:
                logger.error(f"[get_latest_videos] Error fetching data: {response.status}")
                return []

            play_list_data = await response.json()

    if "items" not in play_list_data or not play_list_data["items"]:
        logger.error(f"[get_latest_videos] ❌ No videos found for playlist: {playlist_id}")
        return []

    ret = []
    for vid in play_list_data["items"]:
        vid_snippet = vid["snippet"]
        published_at = vid_snippet["publishedAt"]
        if published_at <= after_timestamp:
            break
        vid_info = {
            "published_at": published_at,
            "video_id": vid_snippet["resourceId"]["videoId"],
            "video_title:": vid_snippet["title"],
            # "video_thumbnail:": vid_snippet["thumbnails"]["default"]["url"],
        }
        ret.append(vid_info)
    return ret

class YouTubeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Ensure the data folder exists before loading channels
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            logger.info(f"Created missing data folder: {DATA_FOLDER}")
        self.player_youtube_info = load_youtube_channels()  # Load channels on startup
        self.check_youtube_task.start()  # Start the background task

        # This is useless, because other bots by default ignore the command sent by any bot account
        # self.invoke_youtube_update_task.start()

    async def check_new_videos(self):
        """
        Return new video list, and update the player info
        """
        new_vid_list = []
        for player_name, player_info in self.player_youtube_info.items():
            last_video_ts = player_info["last_upload_datetime"]
            new_videos = await get_latest_videos(player_info["playlist_id"], last_video_ts)

            if new_videos:
                player_info["last_upload_datetime"] = new_videos[0]["published_at"]
                for video in new_videos:
                    url = f"https://www.youtube.com/watch?v={video['video_id']}"
                    video["player_name"] = player_name
                    video["url"] = url
                    new_vid_list.append(video)
                    logger.info(f"New videos found for player: {player_name}: {url}")

        # Save updated timestamps back to the file
        if new_vid_list:
            logger.info(f"Writing updated info to data file.")
            save_youtube_channels(self.player_youtube_info)

        return new_vid_list

    @tasks.loop(minutes=5)
    async def check_youtube_task(self):
        try:
            new_videos = await self.check_new_videos()
            for video in new_videos:
                discord_video_channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
                await discord_video_channel.send(
                    f"**{video["player_name"]}** has uploaded a new video!\n"
                    f"{video["url"]}"
                )
        except Exception as e:
            logger.exception(f"Error in check_youtube_task: {e}")
            return []

    @check_youtube_task.before_loop
    async def before_check_youtube_task(self):
        """
        Ensure bot is ready before starting the loop.
        """
        await self.bot.wait_until_ready()
        logger.info("Discord bot is ready, starting check_youtube task!")

    @app_commands.command(name="youtube", description="Displays the YouTube channels of the players.")
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    async def youtube(self, interaction):
        if not self.player_youtube_info:
            await interaction.response.send_message("No YouTube channels found.", ephemeral=True)
            return

        youtube_channel_list = sorted([
                {
                    "player_name": player_name,
                    **yt_info
                }
                for player_name, yt_info in self.player_youtube_info.items()
            ],
            key=lambda x: x["last_upload_datetime"],
            reverse=True
        )

        youtube_channel_str = []
        for itm in youtube_channel_list:
            channel_url = f"https://www.youtube.com/channel/{itm['channel_id']}"
            player_name = itm['player_name']
            channel_name = itm['channel_name']
            youtube_channel_str.append(f"**{player_name}**: [{channel_name}]({channel_url})")

        embed = discord.Embed(
            title="Players YouTube Channels",
            description="\n".join(youtube_channel_str),
            color=discord.Color.red()
        )
        embed.set_thumbnail(
            url="https://png.pngtree.com/png-clipart/20221018/ourmid/pngtree-youtube-social-media-3d-stereo-png-image_6308427.png"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addytchannel", description="[Admin only] Adds a YouTube channel for a player.")
    @app_commands.check(is_creator)
    async def addytchannel(self, interaction, player_name: str, handle: str):
        update_player = player_name in self.player_youtube_info  # if already exists, then update, else add
        try_get_indo = await get_youtuber_info(handle)
        if not try_get_indo:
            await interaction.response.send_message(f"❌ Youtuber handle **{handle}** not found.", ephemeral=True)
            return
        self.player_youtube_info[player_name] = await get_youtuber_info(handle)
        save_youtube_channels(self.player_youtube_info)
        if update_player:
            await interaction.response.send_message(f"✅ Updated YouTube channel for **{player_name}**: {handle}", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Added YouTube channel for **{player_name}**: {handle}", ephemeral=True)

    @app_commands.command(name="removeytchannel", description="[Admin only] Removes a YouTube channel from the list.")
    @app_commands.check(is_creator)
    async def removeytchannel(self, interaction, player_name: str):
        if player_name in self.player_youtube_info:
            del self.player_youtube_info[player_name]
            save_youtube_channels(self.player_youtube_info)
            await interaction.response.send_message(f"✅ Removed YouTube channel for **{player_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Player **{player_name}** not found.", ephemeral=True)

    # Periodically invoke the other bot:
    # @tasks.loop(seconds=60)
    # async def invoke_youtube_update_task(self):
    #     await send_a_message_then_delete(self.bot, SEND_MESSAGE_CHANNEL_ID, "!updateyt2000")

    # @invoke_youtube_update_task.before_loop
    # async def before_invoke_youtube_update_task(self):
    #     await self.bot.wait_until_ready()
    #     logger.info("Start invoke_youtube_update task.")

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

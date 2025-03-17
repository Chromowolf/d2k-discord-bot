import logging
import discord
from discord import app_commands
from discord.ext import commands
# noinspection PyPackageRequirements
from google import genai
# noinspection PyPackageRequirements
from google.genai import types
# import asyncio
from config import D2K_SERVER_ID, GEMINI_API_TOKEN
import os

# Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits#free-tier

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)
SYSTEM_PROMPT_PATH = "data/system_prompt_gemini.txt"  # Path to the system prompt file

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)

def load_system_prompt():
    """Loads the system prompt from a text file."""
    if os.path.exists(SYSTEM_PROMPT_PATH):
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as file:
            return file.read().strip()  # Strip to remove extra spaces/newlines
    else:
        logger.warning(f"System prompt file not found at {SYSTEM_PROMPT_PATH}. Using default prompt.")
        return "You are a Discord AI bot. Be helpful and engaging."


class AIChat(commands.Cog):
    """
    A Cog that allows users to interact with an AI model using the `/chat` command.
    """

    def __init__(self, bot):
        self.bot = bot

        # Load system prompt from file
        self.system_prompt = load_system_prompt()

        self.aiclient = genai.Client(api_key=GEMINI_API_TOKEN)

    @app_commands.command(name="chat", description="Start a single-round conversation with the bot.")
    @app_commands.describe(message="Type anything you want to say.")
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))  # 3 times per minute per user
    @app_commands.checks.cooldown(15, 60, key=lambda i: i.guild_id)  # 15 times per minute for all users
    async def chat(self, interaction: discord.Interaction, message: str):
        """Handles the `/chat` command."""
        if interaction.guild is None or interaction.guild.id != D2K_SERVER_ID:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message("This command can only be used in the D2K server.", ephemeral=True)
            return

        # noinspection PyUnresolvedReferences
        await interaction.response.defer()  # Defer response to allow processing time

        try:
            # Generate AI response
            response = await self.aiclient.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    max_output_tokens=500  # Set token limit to prevent exceeding 2000 characters
                    # seed=42,
                ),
            )

            ai_reply = response.text[:1950] if response.text else "I couldn't generate a response. Try again!"

            await interaction.followup.send(ai_reply)

        except Exception as e:
            logger.exception(f"Error in AI chat command: {e}")
            await interaction.followup.send("An error occurred while generating a response. Try again later.", ephemeral=True)


async def setup(bot):
    """Registers the cog with the bot."""
    await bot.add_cog(AIChat(bot), guild=guild)

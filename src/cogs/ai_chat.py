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
# import json
from utils.load_files import load_text_prompt, load_chat_history

# Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits#free-tier
# Doc: https://github.com/google-gemini/generative-ai-python

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

logger.setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)


class AIChat(commands.Cog):
    """
    A Cog that allows users to interact with an AI model using the `/chat` command.
    """

    def __init__(self, bot):
        self.bot = bot

        # Load system prompt from file
        self.system_prompt_short = load_text_prompt()
        chat_history = load_chat_history()
        self.system_prompt_long = f"{self.system_prompt_short} \n Some chat history for you to get familiar to our culture:\n {chat_history}"

        self.models = [
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-2.0-flash",
        ]
        self.model = self.models[0]

        self.aiclient = genai.Client(api_key=GEMINI_API_TOKEN)

    @app_commands.command(name="chat", description="Start a single-round conversation with the bot.")
    @app_commands.describe(message="Type anything you want to say.")
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))  # 3 times per minute per user
    @app_commands.checks.cooldown(10, 60, key=lambda i: i.guild_id)  # 15 times per minute for all users
    async def chat(self, interaction: discord.Interaction, message: str):
        await self.chat_with_prompt(interaction, message, use_chat_history=False)

    @app_commands.command(name="chat2", description="Start a single-round conversation with the bot. Slow than \\chat, but might be smarter.")
    @app_commands.describe(message="Type anything you want to say.")
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))  # 3 times per minute per user
    @app_commands.checks.cooldown(10, 60, key=lambda i: i.guild_id)  # 15 times per minute for all users
    async def chat2(self, interaction: discord.Interaction, message: str):
        await self.chat_with_prompt(interaction, message, use_chat_history=True)

    async def chat_with_prompt(self, interaction: discord.Interaction, message: str, use_chat_history=False):
        """Handles the `/chat` command."""
        try:
            if interaction.guild is None or interaction.guild.id != D2K_SERVER_ID:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message("This command can only be used in the D2K server.", ephemeral=True)
                return

            # Reject messages exceeding 1000 characters
            if len(message) > 1000:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message("Your message cannot exceed 1000 characters.", ephemeral=True)
                return

            # Get user details
            user_nickname = interaction.user.nick or interaction.user.global_name or interaction.user.name
            user_id = interaction.user.id

            # Get timestamp of the message and format it (UTC time)
            timestamp = interaction.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

            # Calculate max output tokens
            max_output_tokens = (2000 - len(message)) // 4  # Ensure a minimum response length

            prompt = (
                f"User (ID: {user_id}, Nickname: {user_nickname}, Timestamp: {timestamp}) says:\n"
                f"```{message}```\n\n"
            )

            logger.debug(f"Sending prompt: \n{prompt}")

            # noinspection PyUnresolvedReferences
            await interaction.response.defer()  # Defer response to allow processing time

            system_prompt = self.system_prompt_long if use_chat_history else self.system_prompt_short
            # Generate AI response
            response = await self.aiclient.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_output_tokens,  # Set token limit to prevent exceeding 2000 characters
                    # seed=42,
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE
                        )
                    ]
                ),
            )

            ai_reply = response.text[:1950] if response.text else "I couldn't generate a response. Try again!"
            response_json = response.to_json_dict()
            total_token_count = response_json.get("usage_metadata", {}).get("total_token_count", 0)
            logger.info(f"Total token count of this request: {total_token_count}")
            logger.debug(f"response info: \n{response.model_dump()}")

            # Format the final output
            final_response = f"**{user_nickname} (at {timestamp}):** {message}\n\n**Response:** {ai_reply}"

            await interaction.followup.send(final_response)

        except Exception as e:
            logger.exception(f"Error in AI chat command: {e}")
            await interaction.followup.send("An error occurred while generating a response. Try again later.", ephemeral=True)


async def setup(bot):
    """Registers the cog with the bot."""
    await bot.add_cog(AIChat(bot), guild=guild)

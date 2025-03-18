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
import json
from utils.load_files import load_text_prompt, load_chat_history
from utils.rate_limiter import MixedRateLimiter
from utils.discord_msg import get_referenced_message, get_recent_messages

from PIL import Image
import aiohttp
from io import BytesIO

# Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits#free-tier
# Doc: https://github.com/google-gemini/generative-ai-python

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

# logger.setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)

async def download_image(url: str) -> Image.Image | None:
    """Asynchronously downloads an image from a URL and returns a PIL Image."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"Failed to download image: {resp.status}")
                    return None
                image_data = await resp.read()
                return Image.open(BytesIO(image_data))
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

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
        self.cooldown_manager = MixedRateLimiter()
        self.cooldown_manager.add_per_user_limit(3, 60)
        self.cooldown_manager.add_per_user_limit(50, 86400)
        self.cooldown_manager.add_global_limit(10, 60)
        self.cooldown_manager.add_global_limit(500, 86400)

    @app_commands.command(name="chat", description="Start a single-round conversation with the bot.")
    @app_commands.describe(message="Type anything you want to say.")
    @app_commands.checks.cooldown(20, 3600, key=lambda i: (i.guild_id, i.user.id))  # 3 times per minute per user
    # @app_commands.checks.cooldown(50, 86400, key=lambda i: (i.guild_id, i.user.id))  # 50 times per day per user
    # @app_commands.checks.cooldown(10, 60, key=lambda i: i.guild_id)  # 15 times per minute for all users
    # @app_commands.checks.cooldown(500, 86400, key=lambda i: i.guild_id)  # 500 times per day for all users
    async def chat(self, interaction: discord.Interaction, message: str):
        await self.chat_with_prompt(interaction, message, use_chat_history=False)

    @app_commands.command(name="chat2", description="Start a single-round conversation with the bot. Slower than /chat, but might be smarter.")
    @app_commands.describe(message="Type anything you want to say.")
    @app_commands.checks.cooldown(20, 3600, key=lambda i: (i.guild_id, i.user.id))  # 3 times per minute per user
    # @app_commands.checks.cooldown(50, 86400, key=lambda i: (i.guild_id, i.user.id))  # 50 times per day per user
    # @app_commands.checks.cooldown(10, 60, key=lambda i: i.guild_id)  # 15 times per minute for all users
    # @app_commands.checks.cooldown(500, 86400, key=lambda i: i.guild_id)  # 500 times per day for all users
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

            # Check against rate limiter
            if not self.cooldown_manager.try_add_message(interaction.user):
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message("You have exceeded the rate limit. Please try again later.", ephemeral=True)
                return

            # Get user details
            user_nickname = interaction.user.nick or interaction.user.global_name or interaction.user.name
            user_id = interaction.user.id

            # Get timestamp of the message and format it (UTC time)
            timestamp = interaction.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

            prompt = (
                f"User (ID: {user_id}, Nickname: {user_nickname}, Timestamp: {timestamp}) says:\n"
                f"{message}"
            )

            logger.info(f"Sending prompt: \n{prompt}")

            # noinspection PyUnresolvedReferences
            await interaction.response.defer()  # Defer response to allow processing time

            # system_prompt = self.system_prompt_long if use_chat_history else self.system_prompt_short
            # # Generate AI response
            # response = await self.aiclient.aio.models.generate_content(
            #     model=self.model,
            #     contents=prompt,
            #     config=types.GenerateContentConfig(
            #         system_instruction=system_prompt,
            #         max_output_tokens=100000,
            #         # seed=42,
            #         safety_settings=[
            #             types.SafetySetting(
            #                 category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            #                 threshold=types.HarmBlockThreshold.BLOCK_NONE
            #             ),
            #             types.SafetySetting(
            #                 category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            #                 threshold=types.HarmBlockThreshold.BLOCK_NONE
            #             ),
            #             types.SafetySetting(
            #                 category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            #                 threshold=types.HarmBlockThreshold.BLOCK_NONE
            #             ),
            #             types.SafetySetting(
            #                 category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            #                 threshold=types.HarmBlockThreshold.BLOCK_NONE
            #             ),
            #             types.SafetySetting(
            #                 category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
            #                 threshold=types.HarmBlockThreshold.BLOCK_NONE
            #             )
            #         ]
            #     ),
            # )
            #
            # ai_reply = response.text if response.text else "I couldn't generate a response. Try again!"
            # response_json = response.to_json_dict()
            # total_token_count = response_json.get("usage_metadata", {}).get("total_token_count", 0)
            # logger.debug(f"Total token count of this request: {total_token_count}")
            # logger.debug(f"response info: \n{json.dumps(response.model_dump(), indent=2)}")

            ai_reply = await self.generate_ai_reply(prompt, use_chat_history=use_chat_history)

            # Format the final output
            final_response = f"**{user_nickname} (at {timestamp}):** {message}\n\n**Response:** {ai_reply}"

            await interaction.followup.send(final_response[:1990])

        except Exception as e:
            logger.exception(f"Error in AI chat command: {e}")
            await interaction.followup.send("An error occurred while generating a response. Try again later.", ephemeral=True)

    async def generate_ai_reply(self, message_content, use_chat_history=False):
        system_prompt = self.system_prompt_long if use_chat_history else self.system_prompt_short
        # Generate AI response
        response = await self.aiclient.aio.models.generate_content(
            model=self.model,
            contents=message_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=100000,
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

        ai_reply = response.text if response.text else "I couldn't generate a response. Try again!"
        response_json = response.to_json_dict()
        total_token_count = response_json.get("usage_metadata", {}).get("total_token_count", 0)
        logger.debug(f"Total token count of this request: {total_token_count}")
        logger.debug(f"response info: \n{json.dumps(response.model_dump(), indent=2)}")

        return ai_reply

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return

            # Check if the message is in the correct guild
            if message.guild is None or message.guild.id != D2K_SERVER_ID:
                return

            # Check if the bot was mentioned
            if self.bot.user not in message.mentions:
                return

            # Check against rate limiter
            if not self.cooldown_manager.try_add_message(message.author):
                await message.reply("You have exceeded the rate limit. Please try again later.")
                return

            # Extract message content
            content = message.content

            # Get user details
            user_nickname = message.author.nick or message.author.global_name or message.author.name
            user_id = message.author.id

            ###################
            # Get contexts
            ###################
            recents = await get_recent_messages(message.channel)
            to_be_sent = ["Recent messages in the channel:"]
            to_be_sent += recents

            rpl = await get_referenced_message(message)
            if rpl:
                rpl_chain = "Reply chain: \n" + "\n".join(rpl)
            else:
                rpl_chain = ""

            to_be_sent.append(rpl_chain)

            # Get timestamp of the message and format it (UTC time)
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

            # Create the latest prompt
            to_be_sent.append(
                f"Latest message for you to reply:\n"
                f"User (ID: {user_id}, Nickname: {user_nickname}, Timestamp: {timestamp}) says:\n"
                f"{content}"
            )

            # Handle image attachments
            images = []
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        image = await download_image(attachment.url)
                        if image:
                            images.append(image)

            logger.info(f"Sending prompt with {len(images)} images: \n")
            for m in to_be_sent:
                logger.info(m)

            # Show typing indicator
            async with message.channel.typing():
                # Use long prompt for more context
                ai_reply = await self.generate_ai_reply(
                    to_be_sent + images,
                    use_chat_history=False
                )
                await message.reply(ai_reply[:1990])

        except Exception as e:
            logger.exception(f"Error in AI chat command: {e}")

async def setup(bot):
    """Registers the cog with the bot."""
    await bot.add_cog(AIChat(bot), guild=guild)

import os
import discord
from discord import app_commands
from pathlib import Path
import logging

# Get the current file's name (e.g., "main.py") and change its extension to ".txt"
file_path = Path(__file__)  # Get the Path object for the current file
log_file = file_path.with_suffix('.log')  # Change the extension to ".log"

logger = logging.getLogger(__name__)  # Currently no handler for "__main__"
logger.setLevel(logging.INFO)  # This level is for the logger itself, not handler.

logging.basicConfig(
    filename="log_file",  # Set a handler to the root logger
    level=logging.INFO,  # Set the level of the root logger to this, not handler. The handler's level is still NOTSET
    format='%(asctime)s %(name)-10s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %z'  # Add timezone info
)

TOKEN = os.getenv('DISCORD_TOKEN')

# Define intents (permissions)
intents = discord.Intents.default()
# intents.message_content = True  # This is needed to read message content


# Create client instance
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        await self.tree.sync()
        logger.info(f"Synced commands for {self.user}")


client = MyClient()


# Define a slash command
@client.tree.command(name="hello", description="Says hello")
async def hello(interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")


# Event for when the bot is ready
@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    logger.info('------')


if __name__ == "__main__":
    try:
        # Run the client
        client.run(TOKEN)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")

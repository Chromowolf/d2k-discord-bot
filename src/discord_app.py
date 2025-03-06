import os
import discord
from discord import app_commands
# from dotenv import load_dotenv

# Load environment variables
# load_dotenv()
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
        print(f"Synced commands for {self.user}")


client = MyClient()


# Define a slash command
@client.tree.command(name="hello", description="Says hello")
async def hello(interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")


# Event for when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


# Run the client
client.run(TOKEN)

import logging
import discord
from discord.ext import commands
from discord import app_commands
from config import D2K_SERVER_ID

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

class BasicCommands(commands.Cog):
    """
    Register all basic commands with the client.
    """

    def __init__(self, bot):
        self.bot = bot

    # @app_commands.command(name="hello", description="Sends a hello message")
    # async def hello_command(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

    @app_commands.command(name="hello1", description="Says hello1")
    async def hello1(self, interaction):
        await interaction.response.send_message(f"Hello again111!, {interaction.user.mention}!")

    # @client.tree.command(name="hello4", description="Says hello (4)", guild=guild)
    # async def hello3(interaction):
    #     await interaction.response.send_message(f"Hello4, {interaction.user.mention}!")

    # @client.tree.command(name="embed", description="Sends an example embed message", guild=guild)
    @app_commands.command(name="embed", description="Sends an example embed message")
    async def embed_example(self, interaction):
        # Create an embed object
        embed = discord.Embed(
            title="Example Embed",
            description="This is an example of an embed message in Discord",
            color=discord.Color.blue()  # Sets a color for the embed's left border
        )

        # Add author information with an icon
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        # Add fields to the embed (name, value, inline)
        embed.add_field(name="Field 1", value="This is the first field", inline=False)
        embed.add_field(name="Field 2", value="This is the second field", inline=True)
        embed.add_field(name="Field 3", value="This is the third field", inline=True)

        # Add a thumbnail image (small image in the top right)
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        # Add a larger image
        # embed.set_image(url="https://example.com/image.png")

        # Add a footer with an icon
        embed.set_footer(text="Sent at " + discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                         icon_url=self.bot.user.display_avatar.url)

        # Send the embed
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BasicCommands(bot), guild=guild)

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

    @app_commands.command(name="hello2d2k", description="Says hello2")
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))
    async def hello2(self, interaction):
        await interaction.response.send_message(f"Hello again222!, {interaction.user.mention}!")

    # @client.tree.command(name="hello4", description="Says hello (4)", guild=guild)
    # async def hello3(interaction):
    #     await interaction.response.send_message(f"Hello4, {interaction.user.mention}!")

    # @client.tree.command(name="embed", description="Sends an example embed message", guild=guild)
    @app_commands.command(name="embedd2k", description="Sends an example embed message")
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

    # handle errors together
    async def cog_app_command_error(self, interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            response = f"You're on cooldown! Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, app_commands.CheckFailure):  # Handles permission errors, etc.
            response = "You don't have permission to use this command!"
        else:
            response = "An unknown error occurred."

        if interaction.response.is_done():
            await interaction.followup.send(response, ephemeral=True)
        else:
            await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BasicCommands(bot), guild=guild)

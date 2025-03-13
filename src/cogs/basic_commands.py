import logging
import discord
from discord.ext import commands
from discord import app_commands
from config import D2K_SERVER_ID
from utils.command_checks import is_bot, is_creator

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

class BasicCommands(commands.Cog):
    """
    Register all basic commands with the client.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hello2d2k", description="Says hello2")
    @app_commands.check(is_bot)
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))
    async def hello2(self, interaction):
        await interaction.response.send_message(f"Hello again222!, {interaction.user.mention}!")

    # @client.tree.command(name="hello4", description="Says hello (4)", guild=guild)
    # async def hello3(interaction):
    #     await interaction.response.send_message(f"Hello4, {interaction.user.mention}!")

    @app_commands.command(name="install", description="How to install Dune2000.")
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    async def install(self, interaction):
        embed = discord.Embed(
            title="Install Dune 2000 for Free",
            description="Here are the installation instructions:",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(
            url="https://media.discordapp.net/attachments/1130464471027044405/1224392395081121994/Dune2000LogoWithGlow.png?ex=661d5347&is=660ade47&hm=65f42ba3fd2280b119ddc3e0066503b2e8e76314203c1fb6d0ca60a4a3fa3859&=&format=webp&quality=lossless")
        embed.add_field(
            name="Windows",
            value="[Download](https://www.mediafire.com/file/zmrkm61izim9s47/Dune2000_All_in_one_Installer.exe/file)",
            inline=False
        )
        embed.add_field(
            name="macOS",
            value="[Download](https://pixeldrain.com/u/ekPz27zX)",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rules", description="Presents the guidelines for 8-Minute No Rush.")
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    async def rules(self, interaction):
        embed = discord.Embed(
            title="Guidelines for 8-Minute No Rush on Habbanya Erg",
            description="Here are the guidelines:",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Allowed Actions",
            value="1. Attacking units on enemy spice fields is permitted, provided that it avoids damage to enemy harvesters. For instance, sniping enemy siege tanks with combat tanks and promptly withdrawing is acceptable.\n"
                  "2. Eliminating enemy harvesters and structures at their expansions is permissible.",
            inline=False
        )
        embed.add_field(
            name="Prohibited Actions",
            value="1. Engaging in any assault on main base buildings and harvesters before the designated timer has elapsed.\n"
                  "2. Lingering in enemy main bases is not allowed, as it can obstruct building placement and disrupt harvester movements.\n"
                  "3. Placing stealth raiders inside enemy refineries is strictly prohibited.",
            inline=False
        )
        embed.set_thumbnail(
            url="https://media.discordapp.net/attachments/1218913633166430231/1224407535717449899/25252.png?ex=661d6160&is=660aec60&hm=c82040d5b680155d23e5f5f51f210d60bc02732482657a3a4681f74ffbd4c504&=&format=webp&quality=lossless")  # Replace with your image URL

        await interaction.response.send_message(embed=embed)

    # @client.tree.command(name="embed", description="Sends an example embed message", guild=guild)
    @app_commands.command(name="embedd2k", description="Sends an example embed message")
    @app_commands.check(is_creator)
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))
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

        # noinspection PyUnresolvedReferences
        if interaction.response.is_done():
            await interaction.followup.send(response, ephemeral=True)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BasicCommands(bot), guild=guild)

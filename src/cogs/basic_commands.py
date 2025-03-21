import logging
import discord
from discord.ext import commands
from discord import app_commands
from config import D2K_SERVER_ID, PLAYER_ONLINE_CHANNEL_ID
# from utils.command_checks import is_creator

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

dune2000_icon_url = "https://media.discordapp.net/attachments/1130464471027044405/1224392395081121994/Dune2000LogoWithGlow.png?ex=661d5347&is=660ade47&hm=65f42ba3fd2280b119ddc3e0066503b2e8e76314203c1fb6d0ca60a4a3fa3859&=&format=webp&quality=lossless"


class BasicCommands(commands.Cog):
    """
    Register all basic commands with the client.
    """

    def __init__(self, bot):
        self.bot = bot

    # @app_commands.command(name="hello2d2k", description="Says hello2")
    # @app_commands.check(is_bot)
    # @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))
    # async def hello2(self, interaction):
    #     await interaction.response.send_message(f"Hello again222!, {interaction.user.mention}!")
    #
    # # @client.tree.command(name="hello4", description="Says hello (4)", guild=guild)
    # # async def hello3(interaction):
    # #     await interaction.response.send_message(f"Hello4, {interaction.user.mention}!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(
                f"Welcome {member.mention} to the spice-filled sands of our Dune 2000 server!\n"
                f"Consider familiarising yourself with the build order for better team game experiences: "
                f"[Tutorial Video](https://www.youtube.com/watch?v=4sUHYgLlbiw)\n"
                f"You can also check who is currently online on CnCNet in this channel: "
                f"https://discord.com/channels/{D2K_SERVER_ID}/{PLAYER_ONLINE_CHANNEL_ID}\n"
                f"For further information about bot commands, type \"/help\""
            )

    @app_commands.command(name="help", description="List all the available commands of the bot.")
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    async def help(self, interaction):
        embed = discord.Embed(
            title="Server Bot Command List",
            description="Here is a list of available commands you can use:",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(
            url=dune2000_icon_url
        )

        embed.add_field(
            name="📥 /install",
            value="Displays how to install **Dune 2000** with installation links.",
            inline=False
        )
        embed.add_field(
            name="📜 /rules",
            value="Presents the **8-Minute No Rush** gameplay guidelines.",
            inline=False
        )
        embed.add_field(
            name="🎭 /excuse",
            value="Generates a **random excuse** for losing a match.",
            inline=False
        )
        embed.add_field(
            name="▶️ /youtube",
            value="Displays the **YouTube channels** of the players.",
            inline=False
        )
        embed.add_field(
            name="💬 /chat & /chat2",
            value="Start a **single-round conversation** with the bot (no memory, no context preservation).",
            inline=False
        )

        embed.set_footer(text="Use slash '/' to see available commands in Discord!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="install", description="How to install Dune2000.")
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    async def install(self, interaction):
        embed = discord.Embed(
            title="Install Dune 2000 for Free",
            description="Here are the installation instructions:",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(
            url=dune2000_icon_url
        )
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
    await bot.add_cog(BasicCommands(bot), guild=guild)

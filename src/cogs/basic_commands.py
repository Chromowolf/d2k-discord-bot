import logging
import discord

logger = logging.getLogger(__name__)


def setup_basic_commands(client):
    """Register all basic commands with the client."""

    @client.tree.command(name="hello", description="Says hello")
    async def hello(interaction):
        await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

    @client.tree.command(name="hello2", description="Says hello (2)")
    async def hello2(interaction):
        await interaction.response.send_message(f"Hello2, {interaction.user.mention}!")

    @client.tree.command(name="embed", description="Sends an example embed message")
    async def embed_example(interaction):
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
                         icon_url=client.user.display_avatar.url)

        # Send the embed
        await interaction.response.send_message(embed=embed)

    logger.info("Basic commands registered")

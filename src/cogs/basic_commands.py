import logging

logger = logging.getLogger(__name__)


def setup_basic_commands(client):
    """Register all basic commands with the client."""

    @client.tree.command(name="hello", description="Says hello")
    async def hello(interaction):
        await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

    logger.info("Basic commands registered")

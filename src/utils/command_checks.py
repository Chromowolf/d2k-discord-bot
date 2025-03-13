import discord
from config import APP_CREATOR_ID  # Ensure this is your actual Discord user ID

def is_bot(interaction: discord.Interaction) -> bool:
    """Check if the command is invoked by the bot itself."""
    return interaction.user.id == interaction.client.user.id

def is_creator(interaction: discord.Interaction) -> bool:
    """Check if the command is invoked by the app creator."""
    return interaction.user.id == APP_CREATOR_ID

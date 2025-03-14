import logging
import discord
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def send_or_update_embed(bot_user_id, channel, embed, content=""):
    """Send a new message or update the latest bot message and delete older ones.

    Args:
        bot_user_id: bot.user.id
        channel: The channel to send/update messages in
        embed: The embed to send
        content: The message content to send
    """
    # Get all messages from the bot in this channel (limited to a reasonable amount)
    bot_messages = []
    async for message in channel.history(limit=10):
        if message.author.id == bot_user_id:
            bot_messages.append(message)

    try:
        if not bot_messages:
            # No existing messages, send a new one
            await channel.send(embed=embed)
        else:
            # Update the most recent message
            latest_message = bot_messages[0]  # First message is the most recent
            await latest_message.edit(content=content, embed=embed)
    except discord.errors.DiscordServerError as e:
        logger.warning(f"Discord server error while sending/updating message: {e}")
    except discord.errors.HTTPException as e:
        logger.warning(f"HTTP error while sending/updating message: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error while sending/updating message: {e}", exc_info=True)

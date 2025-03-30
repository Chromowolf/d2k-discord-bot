import logging
import discord
import asyncio
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
    try:
        # This could raise discord.errors.DiscordServerError: 500 Internal Server Error or 503 Service Unavailable
        async for message in channel.history(limit=5):
            if message.author.id == bot_user_id:
                bot_messages.append(message)
    except discord.errors.DiscordServerError as e:
        logger.warning(f"Discord server error while retreiving message in {channel.name} (ID: {channel.id}). Giving up: {e}")
        return
    except discord.errors.HTTPException as e:
        logger.warning(f"HTTP error while retreiving message in {channel.name} (ID: {channel.id}). Giving up: {e}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error while retreiving message in {channel.name} (ID: {channel.id}). Giving up: {e}")
        return

    try:
        if not bot_messages:
            # No existing messages, send a new one
            await channel.send(embed=embed)
        else:
            # Update the most recent message
            latest_message = bot_messages[0]  # First message is the most recent
            await latest_message.edit(content=content, embed=embed)
    except discord.errors.DiscordServerError as e:
        logger.warning(f"Discord server error while sending/updating message in {channel.name} (ID: {channel.id}): {e}")
    except discord.errors.HTTPException as e:
        logger.warning(f"HTTP error while sending/updating message in {channel.name} (ID: {channel.id}): {e}")
    except Exception as e:
        logger.exception(f"Unexpected error while sending/updating message in {channel.name} (ID: {channel.id}): {e}")


async def send_a_message_then_delete(bot, channel_id, message="Test message", delete_after=5):
    """ Sends a message to a specified channel and deletes it after a delay. """
    channel = bot.get_channel(channel_id)

    if not channel:
        logger.warning(f"Channel with ID {channel_id} not found.")
        return

    try:
        sent_message = await channel.send(message)
        logger.debug(f"Sent message in {channel.name} (ID: {channel.id})")
    except discord.Forbidden:
        logger.error(f"Missing permissions to send messages in {channel.name} (ID: {channel.id})")
        return
    except discord.HTTPException as e:
        logger.error(f"Failed to send message in {channel.name} (ID: {channel.id}): {e}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error when sending message in {channel.name} (ID: {channel.id}): {e}")
        return

    await asyncio.sleep(delete_after)  # Wait before deleting

    try:
        await sent_message.delete()
        logger.debug(f"Deleted message in {channel.name} (ID: {channel.id})")
    except discord.Forbidden:
        logger.error(f"Missing permissions to delete messages in {channel.name} (ID: {channel.id})")
    except discord.HTTPException as e:
        logger.error(f"Failed to delete message in {channel.name} (ID: {channel.id}): {e}")
    except Exception as e:
        logger.exception(f"Unexpected error when deleting message in {channel.name} (ID: {channel.id}): {e}")


def format_message(message: discord.Message):
    """Format a single message for the prompt."""
    user = message.author
    user_id = user.id
    if hasattr(user, "nick"):
        nickname = user.nick
    elif hasattr(user, "global_name"):
        nickname = user.global_name
    else:
        nickname = user.name
    timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

    replied_message = None
    if message.reference and message.reference.resolved:
        replied_message = message.reference.resolved

    replying_to_str = ""
    if replied_message:
        replying_to_str = f" [replying to message: {replied_message.id}]"
    return (
        f"[Message ID: {message.id}] User (ID: {user_id}, Name: {nickname}, Timestamp: {timestamp})"
        f"{replying_to_str}"
        f": {message.content}"
    )


async def get_recent_messages(channel, limit=20) -> list[str]:
    """Get the latest messages from the channel as context."""
    messages = []
    try:
        async for msg in channel.history(limit=limit):
            messages.append(format_message(msg))
    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
        logger.warning(f"Error getting channel context: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error when getting channel context: {e}")

    # Reverse to get chronological order
    messages.reverse()
    return messages


async def get_referenced_message(message: discord.Message, depth=0, max_depth=10) -> list[discord.Message]:
    """
    Recursively get the referenced messages in a reply chain.

    Args:
        message: The Discord message object
        depth: Current depth in the reply chain
        max_depth: Maximum depth to traverse

    Returns:
        The message reply chain in chronological order
    """
    if depth >= max_depth or not message.reference or not message.reference.message_id:
        return []

    try:
        referenced_msg = await message.channel.fetch_message(message.reference.message_id)

        # Recursively get earlier messages in the chain first
        earlier_messages = await get_referenced_message(referenced_msg, depth + 1, max_depth)

        # Return in chronological order (earliest first)
        return earlier_messages + [referenced_msg]

    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
        logger.warning(f"Error fetching referenced message: {e}")
        return []
    except Exception as e:
        logger.exception(f"Unexpected error when fetching referenced message: {e}")
        return []

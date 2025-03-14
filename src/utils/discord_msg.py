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
        return

import discord
from discord.ext import commands, tasks
import asyncio
import threading
import irc.client
import random
import time
import logging
from config import PLAYER_ONLINE_CHANNEL_ID, CNCNET_CHANNEL_KEY


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def escape_discord_formatting(text: str) -> str:
    """Escape characters that trigger Discord's Markdown formatting."""
    special_chars = "\\*_`~|"
    return "".join(f"\\{char}" if char in special_chars else char for char in text)

class Dune2000PlayerMonitor(irc.client.SimpleIRCClient):
    def __init__(self, server, port, nickname, channel, channel_key=None):
        super().__init__()
        self.server = server
        self.port = port
        self.base_nickname = nickname
        self.nickname = nickname
        self.channel = channel
        self.channel_key = channel_key
        self.dune2000_players: list[str] = []
        self.who_event = asyncio.Event()  # Event to signal WHO completion
        self.irc_ready_event = asyncio.Event()  # New event to track IRC readiness (after joining the channel)
        self.registered = False  # connected
        self.join_attempted = False
        self.join_successful = False  # equivalent to self.irc_ready_event.is_set()

        # Prevent UnicodeDecodeError by replacing unrecognized characters
        irc.client.ServerConnection.buffer_class.errors = "replace"

    def on_welcome(self, connection, _):
        """Handles successful connection to IRC."""
        logger.info(f"[IRC] Connected as {self.nickname}. Joining channel {self.channel}")
        self.registered = True
        if self.channel_key:
            connection.join(self.channel, self.channel_key)
        else:
            connection.join(self.channel)
        self.join_attempted = True

    def on_join(self, _, event):
        """Handles successful channel join."""
        if event.source.nick == self.nickname:
            logger.info(f"[IRC] Joined {self.channel}")
            self.join_successful = True
            self.irc_ready_event.set()  # Notify the Discord bot that IRC is ready

    def on_nosuchchannel(self, connection, _):
        logger.info(f"[IRC] Channel {self.channel} does not exist.")
        connection.quit("Invalid channel.")

    def on_badchannelkey(self, connection, _):
        logger.info(f"[IRC] Incorrect key for {self.channel}.")
        connection.quit("Wrong key.")

    def on_nicknameinuse(self, connection, _):
        """Handles nickname conflicts by generating a new one."""
        new_nick = f"{self.base_nickname}{random.randint(100, 999)}"
        self.nickname = new_nick
        logger.info(f"[IRC] Nickname in use, trying {new_nick}")
        connection.nick(new_nick)

    def on_whoreply(self, _, event):
        """Processes WHO replies to extract Dune 2000 players."""
        try:
            line = event.arguments
            if len(line) > 0 and "3 1.40 d2" in line[-1]:  # Identify Dune 2000 players
                # player_name = line[4]
                # country_code = line[2] or "??"
                self.dune2000_players.append(line)
        except UnicodeDecodeError as e:
            logger.warning(f"[IRC] Unicode decode error in WHO reply: {e}")
        except Exception as e:
            logger.exception(f"[IRC] Error processing WHO reply: {e}")

    def on_endofwho(self, _, __):
        """Marks WHO request completion."""
        logger.debug("[IRC] WHO query completed.")
        self.who_event.set()  # Notify waiting coroutines that WHO is complete

    def send_who(self):
        """Requests the WHO list."""
        logger.debug("[IRC] send_who is called!")
        if self.registered:
            logger.debug(f"[IRC] Sending WHO request to {self.channel}")
            self.dune2000_players.clear()  # Reset player list before new WHO request
            self.who_event.clear()  # Reset event before requesting WHO
            self.connection.who(self.channel)

    async def get_players(self, timeout=10) -> list[str]:
        """Waits for WHO response asynchronously and returns the list of players."""
        try:
            await asyncio.wait_for(self.who_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error("[IRC] WHO query timed out.")
        return self.dune2000_players

    def run(self):
        """Connects to the IRC server and starts the reactor loop with a reconnection strategy."""
        logger.info(f"[IRC] Connecting to {self.server}:{self.port} as {self.nickname}")

        max_retries = 150
        base_wait_time = 1  # Start with 1 second and exponentially increase
        max_wait_time = 4000
        attempt = 0

        while attempt < max_retries:  # Stop after 10 failed attempts
            try:
                self.irc_ready_event.clear()  # Mark as unready before attempting connection
                self.registered = False
                self.join_successful = False
                self.connect(self.server, self.port, self.nickname)
                attempt = 0  # Reset retry count since we successfully connected
                self.start()  # This blocks until the connection is lost. (Event loop)

                # If we exit self.start(), it means we were disconnected.
            except irc.client.ServerConnectionError as e:
                if not self.registered:
                    logger.warning(f"[IRC] Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                else:
                    logger.warning(f"[IRC] Connection lost: {e}")
                wait_time = min(base_wait_time * (2 ** attempt), max_wait_time)  # Exponential backoff with max wait time
                logger.warning(f"[IRC] Attempting reconnect in {wait_time} seconds.")
                time.sleep(wait_time)  # Wait before retrying
                attempt += 1
            except Exception as e:
                logger.exception(f"[IRC] Unexpected error occurred, existing event loop. {e}")
                return  # Exit on unexpected exceptions

        logger.critical("[IRC] Max reconnection attempts reached. Giving up.")
        self.stop()

    def stop(self):
        """Gracefully disconnects from IRC."""
        if self.registered:
            self.irc_ready_event.clear()
            logger.info("[IRC] Disconnecting from server...")
            self.connection.disconnect("Bot shutting down.")


class IRCCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.irc_client = Dune2000PlayerMonitor(
            server="irc.gamesurge.net",
            port=6667,
            # nickname="[D2K]Bot",
            nickname="D2kPlayerMonitor",
            channel="#cncnet",
            channel_key=CNCNET_CHANNEL_KEY
        )

        # Note that the following 2 lines are supposed to be in bot.on_ready
        # but too lazy to implement the wrapper.
        # Currently, it sets up the irc thread when the cog is loaded, before the Discord bot is connected.
        self.irc_thread = threading.Thread(target=self.irc_client.run, daemon=True)
        self.irc_thread.start()  # Start IRC in a separate thread

        self.CHANNEL_ID = PLAYER_ONLINE_CHANNEL_ID
        self.who_task.start()  # Start periodic WHO queries

    def cog_unload(self):
        """Stops tasks and disconnects IRC when cog is unloaded."""
        self.who_task.cancel()
        self.irc_client.stop()  # Use stop() instead of nonexistent disconnect()

    async def send_or_update_embed(self, channel, embed, content=""):
        """Send a new message or update the latest bot message and delete older ones.

        Args:
            channel: The channel to send/update messages in
            embed: The embed to send
            content: The message content to send
        """
        # Get all messages from the bot in this channel (limited to a reasonable amount)
        bot_messages = []
        async for message in channel.history(limit=10):
            if message.author.id == self.bot.user.id:
                bot_messages.append(message)

        if not bot_messages:
            # No existing messages, send a new one
            await channel.send(embed=embed)
        else:
            # Update the most recent message
            latest_message = bot_messages[0]  # First message is the most recent
            await latest_message.edit(content=content, embed=embed)

    @tasks.loop(seconds=20)
    async def who_task(self):
        """Requests WHO list and sends results to Discord."""
        # Ensure that IRC is fully connected before sending WHO
        if not self.irc_client.irc_ready_event.is_set():
            logger.info("[IRC] Waiting for IRC connection before sending WHO requests...")
            await self.irc_client.irc_ready_event.wait()  # Wait until IRC is ready

        await asyncio.to_thread(self.irc_client.send_who)  # Send WHO request
        players = await self.irc_client.get_players(timeout=15)  # Wait for response

        channel = self.bot.get_channel(self.CHANNEL_ID)
        if channel:
            # Get current Unix timestamp
            current_timestamp = int(time.time())
            if players:
                # sorted_player_list = sorted(players, key=str.lower)  # Unexpected type(s):(list[str]...
                sorted_player_list = sorted(players, key=lambda s: s.lower())
                # Escape each player's name
                escaped_players_with_status = [
                    ":green_circle: " + escape_discord_formatting(player[4]) if "H" in player[5] else
                    ":red_circle: " + escape_discord_formatting(player[4])
                    for player in sorted_player_list
                ]

                embed = discord.Embed(
                    title=f"{len(escaped_players_with_status)} PLAYERS ONLINE :globe_with_meridians:",
                    description="\n".join(escaped_players_with_status),
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    title=f"NO PLAYERS ONLINE :angry:",
                    description=":sleeping::zzz::cricket::cactus:",
                    color=discord.Color.blue()
                )
            embed.add_field(name="Last Updated", value=f"<t:{current_timestamp}:F>", inline=False)
            await self.send_or_update_embed(channel, embed)
            # if players:
            #     player_list = "\n".join(players)
            #     await channel.send(f"**Dune 2000 Players Online:**\n{player_list}")
            # else:
            #     await channel.send("No Dune 2000 players found online.")
        else:
            logger.error(f"Channel with ID {self.CHANNEL_ID} not found.")

    @who_task.before_loop
    async def before_who_task(self):
        """Waits for the bot and IRC connection before running the task."""
        await self.bot.wait_until_ready()
        logger.info("[Discord] Bot is ready, now waiting for IRC connection...")

        await self.irc_client.irc_ready_event.wait()  # Wait for IRC connection
        logger.info("[IRC] IRC is ready, starting WHO task!")


# Cog setup function
async def setup(bot):
    await bot.add_cog(IRCCog(bot))

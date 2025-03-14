import discord
from discord.ext import commands, tasks
import asyncio
import threading
import irc.client
import random
import time
import logging
from config import PLAYER_ONLINE_CHANNEL_ID, CNCNET_CHANNEL_KEY
import utils.discord_msg as msg_helper


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)


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

        self.running = False  # To control the main event loop

        # Status variables:
        # self.is_connected  # should use self.connection.is_connected()
        self.registered = False  # Set to true when on_welcome, which happens after client.connection.is_connected()
        self.ready_for_who = False  # Equivalent to: joined channel
        self.first_who_completed = False  # At least 1 WHO request succeeded

        # Last disconn:
        self.last_disconnect_time = time.time()

        # Players info
        self._dune2000_players: list[list[str]] = []  # Set to dune2000_players_new_round on end_of_who
        self._dune2000_players_new_round: list[list[str]] = []  # Initiated when sending WHO request

        # Prevent UnicodeDecodeError by replacing unrecognized characters
        irc.client.ServerConnection.buffer_class.errors = "replace"

    def reset_status(self):
        self.registered = False
        self.ready_for_who = False
        self.first_who_completed = False

    def on_welcome(self, connection, _):
        """
        Handles successful connection to IRC.
        Called by the event loop of the IRC client thread
        """
        logger.info(f"[IRC] Connected as {self.nickname}. Joining channel {self.channel}")
        self.registered = True
        if self.channel_key:
            connection.join(self.channel, self.channel_key)
        else:
            connection.join(self.channel)

    def on_join(self, _, event):
        """
        Handles successful channel join.
        Called by the event loop of the IRC client thread
        """
        if event.source.nick == self.nickname:
            logger.info(f"[IRC] Joined {self.channel}")
            self.ready_for_who = True

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
                self._dune2000_players_new_round.append(line)
        except UnicodeDecodeError as e:
            logger.warning(f"[IRC] Unicode decode error in WHO reply: {e}")
        except Exception as e:
            logger.exception(f"[IRC] Error processing WHO reply: {e}")

    def on_endofwho(self, _, __):
        """Marks WHO request completion."""
        logger.debug("[IRC] WHO query completed.")
        self._dune2000_players = self._dune2000_players_new_round.copy()
        self.first_who_completed = True

    def send_who(self):
        """
        Requests the WHO list.
        Called by other threads, so need to handle exceptions here!
        """
        logger.debug("[IRC] send_who is called!")
        if not self.ready_for_who:
            logger.debug("[IRC] send_who is called, but the client is not ready (haven't joined channel yet).")
            return

        try:
            logger.debug(f"[IRC] Sending WHO request to {self.channel}")
            self._dune2000_players_new_round.clear()  # Reset player list before new WHO request
            self.connection.who(self.channel)
        except irc.client.ServerConnectionError as e:
            logger.error(f"[IRC] Connection lost when sending WHO request: {e}")
        except Exception as e:
            logger.exception(f"[IRC] Unexpected error occurred when sending WHO request: {e}")

    def get_players(self):
        return self._dune2000_players

    def on_disconnect(self, _, __):
        self.last_disconnect_time = time.time()
        logger.error("[IRC] Disconnected from server.")

    def connect_and_run(self):
        """
        Starts the connection and runs the event loop, ensuring reconnection if disconnected.
        This must be called in a separate thread!
        The thread ends when self.running becomes False
        """
        self.running = True
        base_wait_time = 1  # Start with 1 second and exponentially increase
        max_wait_time = 3600  # 1 hour
        max_retries = 30 * 86400 // max_wait_time  # 30 days (720 times)
        attempt = 0
        while self.running:  # Stop after centain failed attempts
            if attempt >= max_retries:
                logger.critical("[IRC] Max reconnection attempts reached. Terminating thread...")
                self.stop()  # self.running is set to False inside stop()
                continue
            try:
                self.reset_status()

                logger.info(f"Connecting to {self.server} as {self.nickname}...")
                # connect() is blocking when setting up connection,
                # it may generate irc.client.ServerConnectionError if connection error occurrs at this stage.
                # but it's non-blocking before resgistering, need process_once() to proceed connection.
                self.connect(self.server, self.port, self.nickname)
                logger.info("IRC connection set up, waiting for registration.")
                attempt = 0  # Reset retry count since we successfully connected

                # This event loop breaks in the following cases:
                # (1) connection lost: client.connection.is_connected() is False
                # (2) IRC client manually stopped
                # (3) (Very rare) Connection lost when calling "join", raised irc.client.ServerConnectionError
                # (4) (Very rare) raised other exceptions
                self.start_event_loop()
                logger.info("IRC client's event loop gracefully exited.")
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
                logger.exception(f"[IRC] Unexpected error occurred, Attempting reconnect. {e}")
        logger.info("IRC client stopped. Thread terminated.")

    def start_event_loop(self):
        """Runs the IRC event loop, breaks if disconnected."""
        while self.running:
            if self.connection.is_connected():
                self.reactor.process_once(0.1)
                time.sleep(0.1)  # Prevent CPU overuse. (Unnecessary?)
            else:
                logger.error("[IRC] Connection lost. Exiting event loop...")
                return
        logger.error("[IRC] Client not running. Exiting event loop...")

    def stop(self):
        """Gracefully stops the IRC client."""
        logger.info("Stopping IRC client.")
        if self.connection.is_connected():
            logger.info("Quitting IRC session.")
            self.connection.quit("Shutting down")
        else:
            logger.info("IRC session is not connected anyway.")
        self.reset_status()
        self.running = False  # This will terminate the "connect_and_run" thread


class IRCCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.irc_client = Dune2000PlayerMonitor(
            server="irc.gamesurge.net",
            port=6667,
            nickname="D2kPlayerMonitor",
            channel="#cncnet",
            channel_key=CNCNET_CHANNEL_KEY
        )

        self.irc_thread = threading.Thread(target=self.irc_client.connect_and_run, daemon=True)
        self.irc_thread.start()
        self.CHANNEL_ID = PLAYER_ONLINE_CHANNEL_ID
        self.who_task.start()  # Start periodic WHO queries
        self.print_players_to_discord.start()  # Start print player list

    def cog_unload(self):
        """Stops tasks and disconnects IRC when cog is unloaded."""
        logger.info("unloading IRCCog")
        self.who_task.cancel()
        self.irc_client.stop()  # Can also terminate the irc_thread

    @tasks.loop(seconds=10)
    async def who_task(self):
        """Requests WHO list and sends results to Discord."""
        logger.debug("[Cog] who_task is called!")
        if not self.irc_client.ready_for_who:
            logger.debug("[Cog] who_task is called, but the IRC client is not ready (haven't joined channel yet).")
            return
        # Make it a different thread because the send_who can be blocking for several seconds when connection lost
        # The send_who is not blocking when IRC is connected
        asyncio.create_task(asyncio.to_thread(self.irc_client.send_who))

    @who_task.before_loop
    async def before_who_task(self):
        """Waits for the bot and IRC connection before running the task."""
        await self.bot.wait_until_ready()
        logger.info("[Discord] Bot is ready, starting WHO task!")

    @tasks.loop(seconds=20)
    async def print_players_to_discord(self):
        if not self.irc_client.first_who_completed:
            logger.debug("IRC client is not ready for providing player list.")
            return
        players = self.irc_client.get_players()
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if channel:
            current_timestamp = int(time.time())
            if players:
                sorted_player_list = sorted(players, key=lambda s: s[4].lower())
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
                    title=f"NO PLAYERS ONLINE :rage:",
                    description=":sleeping::zzz::cricket::cactus:",
                    color=discord.Color.blue()
                )
            embed.add_field(name="Last Updated", value=f"<t:{current_timestamp}:F>", inline=False)
            await msg_helper.send_or_update_embed(self.bot.user.id, channel, embed)
        else:
            logger.error(f"Channel with ID {self.CHANNEL_ID} not found.")

    @print_players_to_discord.before_loop
    async def before_print_players_to_discord(self):
        """Waits for the bot and IRC connection before running the task."""
        await self.bot.wait_until_ready()

# Cog setup function
async def setup(bot):
    await bot.add_cog(IRCCog(bot))

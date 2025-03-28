from pathlib import Path
import logging
from bot_client import create_client
from config import DISCORD_TOKEN
from datetime import datetime

# Get the directory where the current script is located
script_dir = Path(__file__).parent

# Create a 'logs' directory beside the script if it doesn't exist
logs_dir = script_dir / 'logs'
logs_dir.mkdir(exist_ok=True)

# Generate a timestamp for the log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create a unique log file for each run
log_file = logs_dir / f'discord_app_{timestamp}.log'

logging.basicConfig(
    filename=log_file,  # Set a handler to the root logger
    level=logging.INFO,  # Set the level of the root logger to this, not handler. The handler's level is still NOTSET
    format='%(asctime)s [%(name)-10s] [%(threadName)s] [%(levelname)-s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %z'  # Add timezone info
)

logger = logging.getLogger(__name__)  # Currently no handler for "__main__"
logger.setLevel(logging.INFO)  # This level is for the logger itself, not handler.

# Suppress INFO logs from 'discord.gateway' by setting its level to WARNING
# Especially suppress "Shard ID None has successfully RESUMED session [session id]"
logging.getLogger("discord.gateway").setLevel(logging.WARNING)

if __name__ == "__main__":
    try:
        client = create_client()
        logger.info("Starting Discord bot...")

        # Run the client
        client.run(DISCORD_TOKEN)

    except Exception as e:
        logger.exception(f"An error occurred while running: {e}")
    finally:
        logger.info("Bot is shutting down")

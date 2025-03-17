import csv
import json
import os
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# File paths
text_file_path = os.path.join("data", "system_prompt_gemini.txt")
csv_file_path = os.path.join("data", "exported_messages.csv")

def load_text_prompt():
    try:
        with open(text_file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        logger.exception(f"Error when loading system prompt: {e}")
        return ""

def load_chat_history(lines=1000):
    try:
        chat_history = []
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            # headers = next(reader)  # Skip the header row

            for i, row in enumerate(reader):
                if i >= lines:  # Stop reading after "lines" rows
                    break

                if len(row) < 5:  # Ensure row has at least 5 columns
                    continue
                timestamp, sender, sender_id, message, reactions = row

                # Process reactions (convert JSON-like string to a proper representation)
                reactions_display = ""
                if reactions.strip():  # Ensure reactions column isn't empty
                    try:
                        parsed_reactions = json.loads(reactions)
                        reactions_display = " | Reactions: " + ", ".join(
                            [f"{emoji} x{count}" for emoji, count in parsed_reactions.items()]
                        )
                    except json.JSONDecodeError:
                        reactions_display = " | Reactions: [Invalid Format]"

                # Format message with optional reactions
                if message.strip() or reactions_display:
                    chat_history.append(f"[{timestamp}] {sender}: {message}{reactions_display}")

        return chr(10).join(chat_history)
    except Exception as e:
        logger.exception(f"Error when loading system prompt: {e}")
        return ""

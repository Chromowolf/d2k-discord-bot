import logging
import discord
from config import D2K_SERVER_ID
import random

logger = logging.getLogger(__name__)
guild = discord.Object(D2K_SERVER_ID)

def generate_excuse():
    # Each excuse is a tuple of (excuse_text, weight)
    # Default weight is 1 for all excuses
    excuses = [
        ("Poopy teammate.", 1),
        ("Bad spot.", 1),
        ("Uncomfortable chair.", 1),
        ("Moldy desk.", 1),
        ("Didn't use keyboard.", 1),
        ("Was having phone call.", 1),
        ("Food was ready.", 1),
        ("Accidentally pressed Esc.", 1),
        ("Kids beside.", 1),
        ("Cat walked across keyboard.", 1),
        ("Lag spike hit at the wrong moment.", 1),
        ("Sun was in my eyes.", 1),
        ("Controller batteries died.", 1),
        ("Someone rang the doorbell.", 1),
        ("My mouse stopped working.", 1),
        ("Broken mouse.", 1),
        ("Was playing with one hand.", 1),
        ("Sneezed at critical moment.", 1),
        ("Discord notification distracted me.", 1),
        ("Too tired to focus.", 1),
        ("Forgot to drink my energy drink.", 1),
        ("Had to use the bathroom urgently.", 1),
        ("Dog wanted attention.", 1),
        ("Roommate turned on vacuum cleaner.", 1),
        ("Hands were cold.", 1),
        ("Headset died mid-game.", 1),
        ("Spilled water on my desk.", 1),
        ("Someone entered my room.", 1),
        ("Internet provider hates me.", 1),
        ("Was texting and playing.", 1),
        ("Screen glare was too intense.", 1),
        ("Wrist started hurting.", 1),
        ("Thought I was playing a different unit.", 1),
        ("Didn't see that coming.", 1),
        ("Mouse DPI changed randomly.", 1),
        ("Keyboard ghosting issues.", 1),
        ("Wasn't actually trying.", 1),
        ("Was streaming and reading chat.", 1),
        ("Power flickered.", 1),
        ("Fingers slipped.", 1),
        ("Forgot to turn off caps lock.", 1),
        ("Monitor went to sleep mode.", 1),
        ("Wasn't warmed up yet.", 1),
        ("Just testing a new strategy.", 1),
        ("Windows update popped up.", 1),
        ("Was eating while playing.", 1),
        ("Neighbor was drilling the wall.", 1),
        ("Weather affected my internet.", 1),
        ("Had hiccups.", 1),
        ("Thought it was practice mode.", 1),
        ("Camera man distracted me.", 1),
        ("Had music on.", 3),
    ]

    # Extract excuses and weights into separate lists
    excuse_texts = [item[0] for item in excuses]
    weights = [item[1] for item in excuses]

    # Use random.choices() which allows for weighted random selection
    # Note: random.choices returns a list, so we take the first element [0]
    return random.choices(excuse_texts, weights=weights, k=1)[0]


def generate_response_format(user, excuse):
    formats = [
        f"{user} says: \"{excuse}\"",
        f"{user}: \"{excuse}\"",
        f"{user} mutters: \"{excuse}\"",
        f"{user} lost because: \"{excuse}\"",
        f"{user} blames their loss on: \"{excuse}\"",
        f"{user}'s excuse: \"{excuse}\"",
        f"\"{excuse}\" - {user}",
        f"{user} would like everyone to know that \"{excuse}\"",
        f"Listen to {user}'s excuse: \"{excuse}\"",
        f"{user} *coughs* \"{excuse}\" *coughs*",
        f"*{user} nervously explains* \"{excuse}\"",
        f"Don't blame {user}, it's just that \"{excuse}\"",
        f"{user} has an announcement: \"{excuse}\"",
        f"{user} wants to clarify: \"{excuse}\"",
        f"According to {user}: \"{excuse}\"",
        f"Breaking news from {user}: \"{excuse}\"",
        f"{user} would like the record to show: \"{excuse}\"",
        f"Let it be known that {user} believes \"{excuse}\"",
        f"{user} swears that \"{excuse}\"",
        f"Today's excuse from {user}: \"{excuse}\"",
        f"{user}: \"{excuse}\" and don't give a f*ck if you don't believe it!",
        f"{user} screams: \"{excuse}\" DEAL WITH IT!",
        f"{user}'s totally legit, not-made-up reason: \"{excuse}\"",
        f"ATTENTION EVERYONE! {user} lost because \"{excuse}\" (obviously)",
        f"{user} would like to present Exhibit A: \"{excuse}\"",
        f"*throws smoke bomb* {user}: \"{excuse}\" *disappears*",
        f"{user}: \"{excuse}\" (Source: Trust me bro)",
        f"{user}: \"{excuse}\" and that's on FACTS.",
        f"The truth according to {user}: \"{excuse}\" - take it or leave it.",
        f"{user} died because \"{excuse}\"... respawning in 3...2...1...",
        f"{user} didn't lose. The game just failed to recognize that \"{excuse}\"",
        f"{user} solemnly swears \"{excuse}\" (with their hand on the Dune 2000 manual)",
        f"{user}: \"{excuse}\" — and I'll die on this hill!",
        f"*Documentary voice* Here we see {user} in their natural habitat, claiming \"{excuse}\"",
        f"{user} has prepared a PowerPoint presentation titled: \"{excuse}\"",
        f"{user} needs everyone to understand that \"{excuse}\" and will not be taking questions.",
        f"{user} slams fist on table: \"{excuse}\" AND THAT'S FINAL!",
        f"Dear Diary, today {user} said \"{excuse}\" and expected us to believe it.",
        f"BREAKING: Local gamer {user} claims \"{excuse}\" - scientists baffled!",
        f"{user} heroically survived despite \"{excuse}\"",
        f"{user} played perfectly but \"{excuse}\" (obviously not their fault)",
        f"{user}: *adjusts glasses* \"Well actually, {excuse}\"",
        f"⚠️ {user}'s official statement: \"{excuse}\" ⚠️",
        f"{user} lost fair and square... SIKE! \"{excuse}\"",
        f"{user}: \"{excuse}\" — prove me wrong, I'll wait."
    ]

    return random.choice(formats)


def setup_excuses(client):
    @client.tree.command(name="excuse", description="Generates a random excuse for losing", guild=guild)
    async def excuse(interaction):
        excuse_text = generate_excuse()
        response = generate_response_format(interaction.user.mention, excuse_text)
        await interaction.response.send_message(response)

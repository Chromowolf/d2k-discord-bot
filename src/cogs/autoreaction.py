import discord
from discord.ext import commands
import re
import random
import logging
from utils.random_event import bernoulli_trial
from utils.rate_limiter import MixedRateLimiter

logger = logging.getLogger(__name__)

class AutoReact(commands.Cog):
    def __init__(self, bot, max_messages=3, cooldown_period=60):
        self.bot = bot
        self.jo_pattern = re.compile(r'\bjo\b', re.IGNORECASE)  # Matches "Jo" or "jo" as a standalone word
        self.cooldown_manager = MixedRateLimiter()
        self.cooldown_manager.add_per_user_limit(max_messages, cooldown_period)
        self.reactions_with_prob = {  # Must Unicode char instead of reaction names
            "🤣": 6,  # :rofl:
            "😂": 3,  # :joy:
            "😹": 1,  # :joy_cat:
        }
        self.choices = list(self.reactions_with_prob.keys())
        self.weights = list(self.reactions_with_prob.values())
        self.prob_having_2nd_reaction = 0.4

        # Customizable cooldown settings (maximum X messages per Y seconds)
        self.max_messages = max_messages
        self.cooldown_period = cooldown_period

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if "Jo" appears as a standalone word
        if not self.jo_pattern.search(message.content):
            return

        # Check against rate limiter
        if not self.cooldown_manager.try_add_message(message.author.id):
            return

        chosen_reactions = []
        first_pick = random.choices(self.choices, weights=self.weights, k=1)[0]
        chosen_reactions.append(first_pick)
        if bernoulli_trial(self.prob_having_2nd_reaction):
            # Remove the selected element and update the choices and weights
            remaining_choices = [k for k in self.reactions_with_prob.keys() if k != first_pick]
            remaining_weights = [self.reactions_with_prob[k] for k in remaining_choices]
            second_pick = random.choices(remaining_choices, weights=remaining_weights, k=1)[0]
            chosen_reactions.append(second_pick)

        try:
            for reaction in chosen_reactions:
                await message.add_reaction(reaction)  # React with 1 or 2 emoji
        except Exception as e:
            logger.exception(
                f"Unexpected error while reacting to message {message.id} in #{message.channel.name} (ID: {message.channel.id}): {e}")

async def setup(bot):
    await bot.add_cog(AutoReact(bot))

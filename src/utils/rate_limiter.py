from collections import defaultdict, deque
import time


class SimpleRateLimiter:
    def __init__(self, rate, per):
        """
        Initialize a rate limit configuration.

        Args:
            rate: Maximum number of messages allowed in the time window
            per: Time window in seconds
        """
        self.rate = rate
        self.per = per

        # Either a global rate limiter (key=None) or a per-user limiter
        self.timestamps_dict = defaultdict(lambda: deque(maxlen=rate))

    def check_limit(self, current_time=None, user_id=None):
        """
        Check if a new message would be allowed under this rate limit,
        without modifying the state.
        Args:
            user_id: If None, then global
            current_time:
        Returns:
            bool: True if allowed, False otherwise
        """
        if current_time is None:
            current_time = time.time()

        timestamps = self.timestamps_dict[user_id]
        # If haven't sent rate yet, allow
        if len(timestamps) < self.rate:
            return True

        # Check if the oldest message is outside the time window
        oldest_timestamp = timestamps[0]
        if current_time - oldest_timestamp > self.per:
            return True

        # Too many messages in the time window
        return False

    def add_timestamp(self, current_time=None, user_id=None):
        """
        Add a timestamp after confirming the message is allowed.
        Args:
            user_id: If None, then global
            current_time:
        """
        if current_time is None:
            current_time = time.time()

        timestamps = self.timestamps_dict[user_id]
        if len(timestamps) >= self.rate:
            timestamps.popleft()  # Remove the oldest timestamp

        timestamps.append(current_time)


class MixedRateLimiter:
    def __init__(self):
        """Initialize a flexible rate limiter with no initial limits."""
        self.global_limiters: list[SimpleRateLimiter] = []
        self.per_user_limiters: list[SimpleRateLimiter] = []

    def add_global_limit(self, rate, per):
        """
        Add a global rate limit.

        Args:
            rate: Maximum number of messages allowed globally in the time window
            per: Time window in seconds
        """
        self.global_limiters.append(SimpleRateLimiter(rate, per))

    def add_per_user_limit(self, rate, per):
        """
        Add a per-user rate limit.

        Args:
            rate: Maximum number of messages allowed per user in the time window
            per: Time window in seconds
        """
        self.per_user_limiters.append(SimpleRateLimiter(rate, per))

    def is_allowed(self, user_id):
        """
        Check if a user is allowed to send a message based on all configured limits,
        without modifying any state.

        Args:
            user_id: The ID of the user

        Returns:
            (bool, str): (True if allowed, None) or (False, reason) if not allowed
        """
        current_time = time.time()

        # Check global limits first
        for limiter in self.global_limiters:
            if not limiter.check_limit(current_time):
                return False

        # Check per-user limits
        for limiter in self.per_user_limiters:
            if not limiter.check_limit(current_time, user_id):
                return False

        return True

    def try_add_message(self, user_id):
        """
        Try to add a message for a user and return whether it was successful.
        Only updates timestamps if all checks pass.

        Args:
            user_id: The ID of the user

        Returns:
            bool
        """
        current_time = time.time()

        # First, check if the message is allowed without modifying state
        allowed = self.is_allowed(user_id)

        if not allowed:
            return False

        # If all checks passed, update all limiters
        for limiter in self.global_limiters:
            limiter.add_timestamp(current_time)

        for limiter in self.per_user_limiters:
            limiter.add_timestamp(current_time, user_id)

        return True

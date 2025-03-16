import random

def bernoulli_trial(p):
    """Returns True with probability p and False with probability (1 - p)."""
    return True if random.random() < p else False

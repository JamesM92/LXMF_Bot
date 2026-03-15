##############################

import time
from commands import register


# Track uptime start time
start_time = time.time()


# -------------------------
# Ping
# -------------------------

@register(
    "ping",
    "Test bot response",
    category="tools",
    cooldown=5   # Short cooldown to prevent spam
)
def ping(args):

    return "pong"


# -------------------------
# Uptime
# -------------------------

@register(
    "uptime",
    "Show bot uptime",
    category="tools",
    cooldown=15   # Prevent frequent spamming
)
def uptime(args):

    seconds = int(time.time() - start_time)

    minutes = seconds // 60
    hours = minutes // 60

    minutes %= 60
    seconds %= 60

    return f"Uptime: {hours}h {minutes}m {seconds}s"

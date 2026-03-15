##############################

import time
from commands import register


# Track uptime start
START_TIME = time.time()


# -------------------------
# Uptime
# -------------------------

@register(
    "uptime",
    "Show node uptime",
    category="community",
    cooldown=60
)
def uptime(args):

    seconds = int(time.time() - START_TIME)

    minutes = seconds // 60
    hours = minutes // 60

    minutes %= 60
    seconds %= 60

    return f"Node Uptime: {hours}h {minutes}m {seconds}s"


# -------------------------
# Node Time
# -------------------------

@register(
    "time",
    "Show node time",
    category="community",
    cooldown=60
)
def node_time(args):

    return time.strftime(
        "Node Time: %Y-%m-%d %H:%M:%S"
    )


# -------------------------
# Echo
# -------------------------

@register(
    "echo",
    "Echo back your message",
    category="community",
    cooldown=60
)
def echo(args):

    if len(args) <= 1:
        return "Usage: echo MESSAGE"

    sender = args[-1]
    message = " ".join(args[:-1])

    return f"{sender}: {message}"


# -------------------------
# Info
# -------------------------

@register(
    "info",
    "Show community node info",
    category="community",
    cooldown=60
)
def info(args):

    return (
        "Community Mesh Node\n"
        "Provides network diagnostics and utility services.\n"
        "Type 'help' for available commands."
    )

import time
from commands import register

@register("whoami", "Show your LXMF address", "network")
def whoami(args):

    sender = args[-1]

    return f"Your LXMF address:\n{sender}"

@register("time", "Show node time", "network")
def node_time(args):

    return time.strftime("Node time: %Y-%m-%d %H:%M:%S")

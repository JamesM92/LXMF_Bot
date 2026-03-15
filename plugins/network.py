from commands import register
import time

@register("time", "Show node time", "network")
def node_time(args):
    return time.strftime("%Y-%m-%d %H:%M:%S")

@register("whoami", "Show your LXMF address", "network")
def whoami(args):
    return f"Your address:\n{args[-1]}"

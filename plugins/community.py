import time
from commands import register

START_TIME = time.time()


@register("uptime", "Show node uptime", "community")
def uptime(args):

    seconds = int(time.time() - START_TIME)

    minutes = seconds // 60
    hours = minutes // 60

    minutes %= 60
    seconds %= 60

    return f"Node Uptime: {hours}h {minutes}m {seconds}s"


@register("time", "Show node time", "community")
def node_time(args):

    return time.strftime("Node Time: %Y-%m-%d %H:%M:%S")


@register("echo", "Echo back your message", "community")
def echo(args):

    if len(args) <= 1:
        return "Usage: echo MESSAGE"

    sender = args[-1]
    message = " ".join(args[:-1])

    return f"{sender}: {message}"


@register("info", "Show community node info", "community")
def info(args):

    return (
        "Community Mesh Node\n"
        "Provides network diagnostics and utility services.\n"
        "Type 'help' for available commands."
    )

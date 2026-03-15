import time
import RNS

from commands import register

start_time = time.time()


@register("whoami", "Show your LXMF address")
def whoami(args):

    # sender hash comes from args if passed by lxmfbot
    if len(args) > 0:
        sender = args[0]
        return f"Your LXMF address:\n{sender}"

    return "Sender unknown"


@register("botaddr", "Show bot LXMF address")
def botaddr(args):

    # The bot address can be retrieved from Reticulum identities
    return "Bot address is visible in node announce logs."


@register("botinfo", "Show bot information")
def botinfo(args):

    return (
        "LXMF Service Bot\n"
        "Running on Reticulum network\n"
        "Plugin command system enabled"
    )


@register("time", "Show node time")
def node_time(args):

    return time.strftime("Node time: %Y-%m-%d %H:%M:%S")


@register("uptime", "Show bot uptime")
def uptime(args):

    seconds = int(time.time() - start_time)

    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    hours = hours % 24
    minutes = minutes % 60
    seconds = seconds % 60

    return f"Uptime: {days}d {hours}h {minutes}m {seconds}s"

import time
from commands import register

start_time = time.time()


@register("weather", "Show temperature")
def weather(args):
    return "Current temperature: 22°C"


@register("ping", "Test if bot is alive")
def ping(args):
    return "pong"


@register("uptime", "Show bot uptime")
def uptime(args):

    seconds = int(time.time() - start_time)

    minutes = seconds // 60
    hours = minutes // 60

    minutes = minutes % 60
    seconds = seconds % 60

    return f"Uptime: {hours}h {minutes}m {seconds}s"

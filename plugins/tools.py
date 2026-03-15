import time
from commands import register

start_time = time.time()

@register("ping", "Test bot response", "tools")
def ping(args):
    return "pong"



@register("uptime", "Show bot uptime", "tools")
def uptime(args):

    seconds = int(time.time() - start_time)

    minutes = seconds // 60
    hours = minutes // 60

    minutes %= 60
    seconds %= 60

    return f"Uptime: {hours}h {minutes}m {seconds}s"

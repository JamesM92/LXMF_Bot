from commands import register


@register(
    "help",
    "Show help menu",
    category="core",
    aliases=["?", "h"],
    cooldown=5
)
def help_cmd(args):
    return None, False

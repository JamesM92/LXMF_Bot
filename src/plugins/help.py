##############################

from commands import register, help_menu, category_help


# -------------------------
# Help Command
# -------------------------

@register(
    "help",
    "Show command categories",
    category="core",
    cooldown=5,
    aliases=["?", "h"]
)
def help_cmd(args):

    if not args:
        return help_menu(1)

    if args[0].isdigit():
        return help_menu(int(args[0]))

    return category_help(args[0])

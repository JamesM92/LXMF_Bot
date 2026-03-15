from commands import register, help_menu

@register("help", "Show help menu", "core")
def help_cmd(args):
    return help_menu()

@register("?", "Show help menu", "core")
def help_short(args):
    return help_menu()

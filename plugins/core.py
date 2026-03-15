from commands import register

@register("help", "Show help menu", "core")
def help_cmd(args):
    from commands import help_menu
    return help_menu()

@register("?", "Show help menu", "core")
def help_short(args):
    from commands import help_menu
    return help_menu()

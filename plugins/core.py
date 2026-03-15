from commands import register, help_menu


@register("help", "Show this menu")
def help_cmd(args):
    return help_menu()


@register("?", "Show this menu")
def help_short(args):
    return help_menu()

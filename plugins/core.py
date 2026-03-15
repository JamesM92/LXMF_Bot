from commands import register, help_menu


# -------------------------
# Help Command
# -------------------------

@register(
    "help",
    "Show full command list",
    category="core",
    cooldown=30   # ⬅ command-level cooldown (seconds)
)
def help_cmd(args):
    return help_menu()


# -------------------------
# Short Help Alias
# -------------------------

@register(
    "?",
    "Show full command list",
    category="core",
    cooldown=30   # ⬅ same cooldown
)
def help_short(args):
    return help_menu()

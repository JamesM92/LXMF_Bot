##############################

from commands import register, admin_login, BOT_INSTANCE


# -------------------------
# Admin Login
# -------------------------

@register(
    "admin",
    "Login as admin",
    category="admin",
    cooldown=30
)
def admin_cmd(args):

    if len(args) < 2:
        return "Usage: admin PASSWORD", True

    password = args[0]
    sender = args[-1]

    success, msg = admin_login(sender, password)

    return msg, True


# -------------------------
# Lockdown Toggle (Admin Only)
# -------------------------

@register(
    "lockdown",
    "Toggle lockdown mode",
    category="admin",
    admin=True
)
def lockdown(args):

    bot = BOT_INSTANCE

    if bot is None:
        return "Bot not initialized.", True

    status = bot.toggle_lockdown()

    if status:
        return "🔒 Lockdown ON", True
    else:
        return "🔓 Lockdown OFF", True


# -------------------------
# Stats Command (Admin Only)
# -------------------------

@register(
    "stats",
    "Show usage statistics",
    category="admin",
    admin=True
)
def stats(args):

    bot = BOT_INSTANCE

    if bot is None:
        return "Bot not initialized.", True

    stats_data = bot.state["stats"]

    return (
        "📊 Stats\n"
        f"Total Commands: {stats_data['total']}\n"
        f"Unique Users: {len(stats_data['per_user'])}\n"
        f"Unique Commands: {len(stats_data['per_command'])}"
    ), True

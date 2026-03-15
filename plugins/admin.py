from commands import register, admin_login, is_admin, BOT_INSTANCE


# -------------------------
# Admin Login Command
# -------------------------

@register("admin", "Login as admin", "admin")
def admin_cmd(args):

    if len(args) < 2:
        return "Usage: admin PASSWORD", True

    password = args[0]
    sender = args[-1]

    success, msg = admin_login(sender, password)

    return msg, True


# -------------------------
# Lockdown Toggle
# -------------------------

@register("lockdown", "Toggle lockdown mode", "admin", admin=True)
def lockdown(args):

    bot = BOT_INSTANCE

    if bot is None:
        return "Bot not initialized.", True

    status = bot.toggle_lockdown()

    return "🔒 Lockdown ON" if status else "🔓 Lockdown OFF", True


# -------------------------
# Stats Command
# -------------------------

@register("stats", "Show usage statistics", "admin", admin=True)
def stats(args):

    bot = BOT_INSTANCE

    if bot is None:
        return "Bot not initialized.", True

    stats_data = bot.state["stats"]

    return (
        f"📊 Stats\n"
        f"Total: {stats_data['total']}\n"
        f"Users: {len(stats_data['per_user'])}\n"
        f"Commands: {len(stats_data['per_command'])}",
        True
    )

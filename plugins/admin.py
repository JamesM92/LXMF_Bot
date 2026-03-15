from commands import register
from commands import BOT_INSTANCE, admin_login, is_admin

@register("admin", "Login as admin", "admin")
def admin_cmd(args):

    if len(args) < 2:
        return "Usage: admin PASSWORD"

    password = args[0]
    sender = args[-1]

    success, msg = admin_login(sender, password)

    return msg


@register("lockdown", "Toggle lockdown mode", "admin", admin=True)
def lockdown(args):

    bot = BOT_INSTANCE

    status = bot.toggle_lockdown()

    return "🔒 Lockdown ON" if status else "🔓 Lockdown OFF"


@register("stats", "Show usage statistics", "admin", admin=True)
def stats(args):

    bot = BOT_INSTANCE
    stats = bot.state["stats"]

    return (
        f"📊 Stats\n"
        f"Total: {stats['total']}\n"
        f"Users: {len(stats['per_user'])}\n"
        f"Commands: {len(stats['per_command'])}"
    )

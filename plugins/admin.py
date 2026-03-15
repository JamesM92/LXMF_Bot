from commands import register, reload_plugins, is_admin, admin_login


@register("admin", "Authenticate as admin (admin PASSWORD)")
def admin_auth(args):

    if len(args) < 2:
        return "Usage: admin PASSWORD"

    password = args[0]
    sender = args[-1]

    success, message = admin_login(sender, password)

    return message


@register("adminstatus", "Check admin session status")
def admin_status(args):

    sender = args[-1]

    if is_admin(sender):
        return "Admin session active."

    return "You are not authenticated."


@register("reload", "Reload plugins (admin)")
def reload_cmd(args):

    sender = args[-1]

    if not is_admin(sender):
        return "Admin only command."

    reload_plugins()

    return "Plugins reloaded."

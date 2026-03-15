from commands import register, reload_plugins, admin_login

@register("admin", "Authenticate admin session", "admin")
def admin_auth(args):

    if len(args) < 2:
        return "Usage: admin PASSWORD"

    password = args[0]
    sender = args[-1]

    success, message = admin_login(sender, password)

    return message


@register("reload", "Reload plugins", "admin", admin=True)
def reload_cmd(args):

    reload_plugins()

    return "Plugins reloaded."

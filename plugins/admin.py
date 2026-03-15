from commands import register, admin_login, is_admin

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

    from lxmfbot import LXMFBot

    return "Lockdown feature available in state system."

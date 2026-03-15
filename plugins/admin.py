from commands import register, admin_login, is_admin


@register("login", "Authenticate as admin", "admin")
def login(args):

    if len(args) < 2:
        return "Usage: login <password>", True

    password = args[0]
    sender = args[1]

    success, message = admin_login(sender, password)

    return message, True




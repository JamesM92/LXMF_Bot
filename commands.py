import importlib
import os
import hashlib
import time

COMMANDS = {}

ADMIN_ADDRESSES = {"PUT_LXMF_ADDRESS_HERE"}
ADMIN_PASSWORD_HASH = hashlib.sha256("changeme".encode()).hexdigest()

ACTIVE_ADMINS = {}
LOGIN_COOLDOWN = {}


class Command:
    def __init__(self, name, func, desc, category="general", admin=False):
        self.name = name
        self.func = func
        self.desc = desc
        self.category = category
        self.admin = admin


def register(name, desc, category="general", admin=False):
    def wrapper(func):
        COMMANDS[name] = Command(name, func, desc, category, admin)
        return func
    return wrapper


def is_admin(sender):

    if sender in ADMIN_ADDRESSES:
        return True

    if sender in ACTIVE_ADMINS and ACTIVE_ADMINS[sender] > time.time():
        return True

    return False


def admin_login(sender, password):

    now = time.time()

    if LOGIN_COOLDOWN.get(sender, 0) > now:
        return False, "Login cooldown active."

    LOGIN_COOLDOWN[sender] = now + 30

    if hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
        ACTIVE_ADMINS[sender] = now + 1800
        return True, "Admin authenticated."

    return False, "Invalid password."


def handle_command(message, sender):

    parts = message.strip().split()

    if not parts:
        return help_menu(), False

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in COMMANDS:

        if COMMANDS[cmd].admin and not is_admin(sender):
            return "Admin only.", True

        try:
            return COMMANDS[cmd].func(args + [sender]), True
        except:
            return "Command error.", True

    return help_menu(), False


def help_menu():

    out = ["Commands:\n"]

    for cmd in sorted(COMMANDS):
        out.append(f"{cmd} - {COMMANDS[cmd].desc}")

    return "\n".join(out)


def load_plugins():

    for file in os.listdir("plugins"):
        if file.endswith(".py") and file != "__init__.py":
            importlib.import_module(f"plugins.{file[:-3]}")


load_plugins()

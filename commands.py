import os
import importlib
import time
import hashlib

COMMANDS = {}

# Admin configuration
ADMIN_ADDRESSES = {
    "PUT_ADMIN_LXMF_ADDRESS_HERE"
}

# hashed password (generate with sha256)
ADMIN_PASSWORD_HASH = "PUT_SHA256_HASH_HERE"

# session settings
ADMIN_SESSION_DURATION = 1800  # 30 minutes
LOGIN_COOLDOWN = 30  # seconds between attempts

ACTIVE_ADMINS = {}
LOGIN_ATTEMPTS = {}


class Command:
    def __init__(self, name, function, description):
        self.name = name
        self.function = function
        self.description = description


def register(name, description):
    def wrapper(func):
        COMMANDS[name] = Command(name, func, description)
        return func
    return wrapper


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def is_admin(sender):

    # permanent admin
    if sender in ADMIN_ADDRESSES:
        return True

    # temporary session
    if sender in ACTIVE_ADMINS:

        expire = ACTIVE_ADMINS[sender]

        if time.time() < expire:
            return True
        else:
            del ACTIVE_ADMINS[sender]

    return False


def admin_login(sender, password):

    now = time.time()

    # throttle login attempts
    last_attempt = LOGIN_ATTEMPTS.get(sender, 0)

    if now - last_attempt < LOGIN_COOLDOWN:
        return False, "Login temporarily blocked. Please wait."

    LOGIN_ATTEMPTS[sender] = now

    if hash_password(password) == ADMIN_PASSWORD_HASH:

        ACTIVE_ADMINS[sender] = now + ADMIN_SESSION_DURATION

        return True, "Admin authentication successful."

    return False, "Invalid password."


def load_plugins():

    plugin_dir = "plugins"

    if not os.path.isdir(plugin_dir):
        return

    for file in os.listdir(plugin_dir):

        if file.endswith(".py") and file != "__init__.py":

            module_name = f"plugins.{file[:-3]}"
            importlib.import_module(module_name)


def reload_plugins():

    global COMMANDS
    COMMANDS.clear()

    for module in list(importlib.sys.modules.keys()):
        if module.startswith("plugins."):
            del importlib.sys.modules[module]

    load_plugins()


def handle_command(message, sender=None):

    parts = message.strip().split()

    if len(parts) == 0:
        return help_menu(), False

    cmd = parts[0].lower()
    args = parts[1:]

    if sender:
        args.append(sender)

    if cmd in COMMANDS:

        try:
            return COMMANDS[cmd].function(args), True
        except Exception:
            return "Command error.", True

    return help_menu(), False


def help_menu():

    output = ["Available Commands:\n"]

    for name in sorted(COMMANDS):
        output.append(f"{name} - {COMMANDS[name].description}")

    return "\n".join(output)


load_plugins()

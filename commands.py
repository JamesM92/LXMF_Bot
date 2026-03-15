import os
import importlib
import time
import hashlib

COMMANDS = {}
PLUGINS = {}

# admin config
ADMIN_ADDRESSES = {"PUT_ADMIN_LXMF_ADDRESS"}
ADMIN_PASSWORD_HASH = "PUT_HASH"

ADMIN_SESSION_DURATION = 1800
LOGIN_COOLDOWN = 30

ACTIVE_ADMINS = {}
LOGIN_ATTEMPTS = {}


class Command:

    def __init__(self, name, function, description, category="general", admin=False):

        self.name = name
        self.function = function
        self.description = description
        self.category = category
        self.admin = admin


def register(name, description, category="general", admin=False):

    def wrapper(func):

        COMMANDS[name] = Command(name, func, description, category, admin)

        return func

    return wrapper


def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest()


def is_admin(sender):

    if sender in ADMIN_ADDRESSES:
        return True

    if sender in ACTIVE_ADMINS:

        expire = ACTIVE_ADMINS[sender]

        if time.time() < expire:
            return True

        del ACTIVE_ADMINS[sender]

    return False


def admin_login(sender, password):

    now = time.time()

    last_attempt = LOGIN_ATTEMPTS.get(sender, 0)

    if now - last_attempt < LOGIN_COOLDOWN:
        return False, "Login temporarily blocked."

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

            module = file[:-3]

            module_name = f"plugins.{module}"

            importlib.import_module(module_name)

            PLUGINS[module] = True


def reload_plugins():

    global COMMANDS

    COMMANDS.clear()

    for module in list(importlib.sys.modules.keys()):

        if module.startswith("plugins."):

            del importlib.sys.modules[module]

    load_plugins()


def enable_plugin(name):

    if name in PLUGINS:
        PLUGINS[name] = True
        reload_plugins()


def disable_plugin(name):

    if name in PLUGINS:
        PLUGINS[name] = False
        reload_plugins()


def handle_command(message, sender=None):

    parts = message.strip().split()

    if not parts:
        return help_menu(), False

    cmd = parts[0].lower()
    args = parts[1:]

    if sender:
        args.append(sender)

    if cmd not in COMMANDS:
        return help_menu(), False

    command = COMMANDS[cmd]

    if command.admin and not is_admin(sender):
        return "Admin only command.", True

    try:
        return command.function(args), True

    except Exception:
        return "Command error.", True


def help_menu():

    categories = {}

    for cmd in COMMANDS.values():

        categories.setdefault(cmd.category, []).append(cmd)

    output = ["Available Commands:\n"]

    for cat in sorted(categories):

        output.append(f"\n[{cat}]")

        for c in sorted(categories[cat], key=lambda x: x.name):
            output.append(f"{c.name} - {c.description}")

    return "\n".join(output)


load_plugins()

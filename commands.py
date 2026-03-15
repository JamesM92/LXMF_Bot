##############################

import importlib
import os
import time
import hashlib

COMMANDS = {}
BOT_INSTANCE = None

ADMIN_ADDRESSES = {"PUT_LXMF_ADDRESS_HERE"}
ADMIN_PASSWORD_HASH = hashlib.sha256("changeme".encode()).hexdigest()

ACTIVE_ADMINS = {}
LOGIN_COOLDOWN = {}


def set_bot(bot):
    global BOT_INSTANCE
    BOT_INSTANCE = bot


def register(name, desc, category="general", admin=False):

    def wrapper(func):
        COMMANDS[name] = {
            "func": func,
            "desc": desc,
            "category": category,
            "admin": admin
        }
        return func

    return wrapper


def is_admin(sender):

    if sender in ADMIN_ADDRESSES:
        return True

    if sender in ACTIVE_ADMINS and ACTIVE_ADMINS[sender] > time.time():
        return True

    return False


def handle_command(message, sender):

    parts = message.strip().split()

    if not parts:
        return help_menu(), False

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd not in COMMANDS:
        return help_menu(), False

    entry = COMMANDS[cmd]

    if entry["admin"] and not is_admin(sender):
        return "Admin only.", True

    try:
        return entry["func"](args + [sender]), True
    except Exception as e:
        return f"Command error: {repr(e)}", True


def help_menu():

    out = ["Commands:\n"]

    for cmd in sorted(COMMANDS):
        out.append(f"{cmd} - {COMMANDS[cmd]['desc']}")

    return "\n".join(out)


# -------------------------
# Plugin Loader (CALLED FROM BOT)
# -------------------------

def load_plugins():

    plugin_path = os.path.join(os.path.dirname(__file__), "plugins")

    if not os.path.isdir(plugin_path):
        return

    for file in os.listdir(plugin_path):
        if file.endswith(".py") and file != "__init__.py":
            importlib.import_module(f"plugins.{file[:-3]}")

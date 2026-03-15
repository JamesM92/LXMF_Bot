##############################

import importlib
import os
import time
import hashlib

COMMANDS = {}
BOT_INSTANCE = None

ADMIN_ADDRESSES = {"PUT_LXMF_ADDRESS_HERE"}

ADMIN_PASSWORD_HASH = hashlib.sha256(
    "changeme".encode()
).hexdigest()

ACTIVE_ADMINS = {}
LOGIN_COOLDOWN = {}


# -------------------------
# Bot Reference
# -------------------------

def set_bot(bot):
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# -------------------------
# Command Registration
# -------------------------

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


# -------------------------
# Admin Check
# -------------------------

def is_admin(sender):

    if sender in ADMIN_ADDRESSES:
        return True

    if sender in ACTIVE_ADMINS and ACTIVE_ADMINS[sender] > time.time():
        return True

    return False


# -------------------------
# Admin Login
# -------------------------

def admin_login(sender, password):

    now = time.time()

    if LOGIN_COOLDOWN.get(sender, 0) > now:
        return False, "Login cooldown active."

    LOGIN_COOLDOWN[sender] = now + 30

    if hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
        ACTIVE_ADMINS[sender] = now + 1800
        return True, "Admin authenticated."

    return False, "Invalid password."


# -------------------------
# Command Handler
# -------------------------

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
        result = entry["func"](args + [sender])
        return result, True
    except Exception as e:
        return f"Command error: {repr(e)}", True


# -------------------------
# Help Menu
# -------------------------

def help_menu():

    out = ["Commands:\n"]

    for cmd in sorted(COMMANDS):
        out.append(f"{cmd} - {COMMANDS[cmd]['desc']}")

    return "\n".join(out)


# -------------------------
# Plugin Loader
# -------------------------

def load_plugins():

    plugin_path = os.path.join(
        os.path.dirname(__file__),
        "plugins"
    )

    if not os.path.isdir(plugin_path):
        return

    for file in os.listdir(plugin_path):
        if file.endswith(".py") and file != "__init__.py":
            importlib.import_module(
                f"plugins.{file[:-3]}"
            )

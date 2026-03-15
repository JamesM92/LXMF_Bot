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
# Register Command
# -------------------------

def register(name, desc, category="general", admin=False, cooldown=60):

    def wrapper(func):
        COMMANDS[name] = {
            "func": func,
            "desc": desc,
            "category": category,
            "admin": admin,
            "cooldown": cooldown
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
# Grouped Help Menu
# -------------------------

def help_menu():

    if not COMMANDS:
        return "No commands available."

    grouped = {}

    for cmd, entry in COMMANDS.items():
        category = entry.get("category", "general")
        grouped.setdefault(category, []).append((cmd, entry))

    output = ["Commands:\n"]

    for category in sorted(grouped):

        output.append(f"\n📦 {category.upper()}")

        for cmd, entry in sorted(grouped[category]):
            admin_flag = " (admin)" if entry.get("admin") else ""
            output.append(f"  • {cmd}{admin_flag} - {entry['desc']}")

    return "\n".join(output)


# -------------------------
# Handle Commands
# -------------------------

def handle_command(message, sender):

    parts = message.strip().split()

    if not parts:
        return help_menu(), False

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd not in COMMANDS:
        return None, False  # handled in bot layer

    entry = COMMANDS[cmd]

    if entry["admin"] and not is_admin(sender):
        return "Admin only.", True

    try:
        result = entry["func"](args + [sender])
        return result, True
    except Exception as e:
        return f"Command error: {repr(e)}", True


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

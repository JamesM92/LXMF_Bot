##############################

import importlib
import os
import sys
import time
import hashlib

COMMANDS = {}
BOT_INSTANCE = None

# =====================================================
# Command Registration (MUST BE AT TOP)
# =====================================================

def register(name, desc, category="general", admin=False, cooldown=60, aliases=None):

    if aliases is None:
        aliases = []

    def wrapper(func):

        COMMANDS[name] = {
            "func": func,
            "desc": desc,
            "category": category,
            "admin": admin,
            "cooldown": cooldown
        }

        for alias in aliases:
            COMMANDS[alias] = name

        return func

    return wrapper


# =====================================================
# Bot Reference
# =====================================================

def set_bot(bot):
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# =====================================================
# Plugin System (Hot Reload Safe)
# =====================================================

PLUGIN_DIR = os.path.join(
    os.path.dirname(__file__),
    "plugins"
)

PLUGIN_MODULES = {}
PLUGIN_MTIMES = {}

PLUGIN_SCAN_INTERVAL = 5
LAST_PLUGIN_SCAN = 0


def scan_plugins(force=False):

    global LAST_PLUGIN_SCAN

    now = time.time()

    if not force and (now - LAST_PLUGIN_SCAN) < PLUGIN_SCAN_INTERVAL:
        return

    LAST_PLUGIN_SCAN = now

    if not os.path.isdir(PLUGIN_DIR):
        return

    current_files = {
        f for f in os.listdir(PLUGIN_DIR)
        if f.endswith(".py") and f != "__init__.py"
    }

    # Load or reload
    for file in current_files:

        module_name = f"plugins.{file[:-3]}"
        path = os.path.join(PLUGIN_DIR, file)

        try:
            mtime = os.path.getmtime(path)
        except FileNotFoundError:
            continue

        if module_name not in sys.modules:

            importlib.import_module(module_name)
            PLUGIN_MODULES[module_name] = True
            PLUGIN_MTIMES[module_name] = mtime
            continue

        if PLUGIN_MTIMES.get(module_name, 0) < mtime:

            importlib.reload(sys.modules[module_name])
            PLUGIN_MTIMES[module_name] = mtime

    # Remove deleted
    for module_name in list(PLUGIN_MODULES.keys()):

        file_name = module_name.split(".")[-1] + ".py"

        if file_name not in current_files:

            if module_name in sys.modules:
                del sys.modules[module_name]

            del PLUGIN_MODULES[module_name]
            del PLUGIN_MTIMES[module_name]


def load_plugins():
    scan_plugins(force=True)


# =====================================================
# Admin System
# =====================================================

ADMIN_ADDRESSES = {"PUT_LXMF_ADDRESS_HERE"}

ADMIN_PASSWORD_HASH = hashlib.sha256(
    "changeme".encode()
).hexdigest()

ACTIVE_ADMINS = {}
LOGIN_COOLDOWN = {}


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


# =====================================================
# Command Handler
# =====================================================

def handle_command(message, sender):

    scan_plugins()

    parts = message.strip().split()

    if not parts:
        return None, False

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd not in COMMANDS:
        return None, False

    entry = COMMANDS[cmd]

    if isinstance(entry, str):
        cmd = entry
        entry = COMMANDS[cmd]

    if entry["admin"] and not is_admin(sender):
        return "Admin only.", True

    try:
        result = entry["func"](args + [sender])
        return result, True
    except Exception as e:
        return f"Command error: {repr(e)}", True

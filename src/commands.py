import importlib
import os
import sys
import time
import hashlib

COMMANDS = {}
BOT_INSTANCE = None

# =====================================================
# Registration
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


def set_bot(bot):
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# =====================================================
# Admin System
# =====================================================

ADMIN_ADDRESSES = {"PUT_LXMF_ADDRESS_HERE"}

ADMIN_PASSWORD_HASH = hashlib.sha256("changeme".encode()).hexdigest()

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
# Plugin Hot Reload
# =====================================================

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")

_loaded = {}
_mtimes = {}
_last_scan = 0
SCAN_INTERVAL = 5


def scan_plugins(force=False):

    global _last_scan

    now = time.time()

    if not force and (now - _last_scan) < SCAN_INTERVAL:
        return

    _last_scan = now

    if not os.path.isdir(PLUGIN_DIR):
        return

    current_files = {
        f for f in os.listdir(PLUGIN_DIR)
        if f.endswith(".py") and f != "__init__.py"
    }

    for file in current_files:

        module_name = f"plugins.{file[:-3]}"
        path = os.path.join(PLUGIN_DIR, file)

        try:
            mtime = os.path.getmtime(path)
        except FileNotFoundError:
            continue

        if module_name not in sys.modules:
            importlib.import_module(module_name)
            _loaded[module_name] = True
            _mtimes[module_name] = mtime
            continue

        if _mtimes.get(module_name, 0) < mtime:
            importlib.reload(sys.modules[module_name])
            _mtimes[module_name] = mtime

    for module_name in list(_loaded.keys()):
        filename = module_name.split(".")[-1] + ".py"
        if filename not in current_files:
            if module_name in sys.modules:
                del sys.modules[module_name]
            del _loaded[module_name]
            del _mtimes[module_name]


def load_plugins():
    scan_plugins(force=True)


# =====================================================
# Command Handler (Cooldown + Admin Safe)
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
        result = entry["func"](args)
        if isinstance(result, tuple):
            return result
        return result, True
    except Exception as e:
        return f"Command error: {repr(e)}", True

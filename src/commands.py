import importlib
import importlib.util
import os
import sys
import time
import hashlib
import inspect

# =====================================================
# Registry
# =====================================================

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
# Plugin System
# =====================================================

BASE_DIR = os.path.dirname(__file__)

PLUGIN_DIRS = [
    os.path.join(BASE_DIR, "plugins"),                 # built-in plugins
    os.path.expanduser("~/.config/lxmfbot/plugins"),   # external plugins
]

# Ensure directories exist
for d in PLUGIN_DIRS:
    os.makedirs(d, exist_ok=True)


_loaded = {}
_mtimes = {}
_last_scan = 0
SCAN_INTERVAL = 5


# =====================================================
# Plugin Loader
# =====================================================

def _load_plugin(module_name, path):

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module


# =====================================================
# Plugin Scanner
# =====================================================

def scan_plugins(force=False):

    global _last_scan

    now = time.time()

    if not force and (now - _last_scan) < SCAN_INTERVAL:
        return

    _last_scan = now

    for plugin_dir in PLUGIN_DIRS:

        if not os.path.isdir(plugin_dir):
            continue

        for file in os.listdir(plugin_dir):

            if not file.endswith(".py") or file.startswith("_"):
                continue

            path = os.path.join(plugin_dir, file)

            module_name = f"lxmfbot_plugin_{file[:-3]}"

            try:

                mtime = os.path.getmtime(path)

                # First load
                if module_name not in sys.modules:

                    module = _load_plugin(module_name, path)

                    _loaded[module_name] = True
                    _mtimes[module_name] = mtime

                    print(f"Loaded plugin: {file}")

                # Hot reload
                else:

                    if _mtimes.get(module_name, 0) < mtime:

                        importlib.reload(sys.modules[module_name])
                        _mtimes[module_name] = mtime

                        print(f"Reloaded plugin: {file}")

            except Exception as e:

                print(f"Plugin error ({file}): {e}")


def load_plugins():
    scan_plugins(force=True)


# =====================================================
# Command Execution
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

    # Alias resolution
    if isinstance(entry, str):
        cmd = entry
        entry = COMMANDS[cmd]

    # Admin check
    if entry["admin"] and not is_admin(sender):
        return "Admin only.", True

    try:

        func = entry["func"]
        sig = inspect.signature(func)

        if len(sig.parameters) == 2:
            result = func(args, sender)
        else:
            result = func(args)

        if isinstance(result, tuple):
            return result

        return result, True

    except Exception as e:

        return f"Command error: {repr(e)}", True

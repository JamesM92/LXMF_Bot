import importlib
import os
import time
import hashlib
import sys

COMMANDS = {}
BOT_INSTANCE = None

# -------------------------
# Plugin Tracking
# -------------------------

PLUGIN_MODULES = {}
PLUGIN_MTIMES = {}

PLUGIN_DIR = os.path.join(
    os.path.dirname(__file__),
    "plugins"
)

# How often to check for changes (seconds)
PLUGIN_SCAN_INTERVAL = 5
LAST_PLUGIN_SCAN = 0


# -------------------------
# Bot Reference
# -------------------------

def set_bot(bot):
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# -------------------------
# Hot Reload System
# -------------------------

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

    # -------------------------
    # Load New / Modified
    # -------------------------

    for file in current_files:

        path = os.path.join(PLUGIN_DIR, file)
        mtime = os.path.getmtime(path)
        module_name = f"plugins.{file[:-3]}"

        # New plugin
        if module_name not in PLUGIN_MODULES:

            module = importlib.import_module(module_name)
            PLUGIN_MODULES[module_name] = module
            PLUGIN_MTIMES[module_name] = mtime
            continue

        # Modified plugin
        if PLUGIN_MTIMES.get(module_name, 0) < mtime:

            module = PLUGIN_MODULES[module_name]
            importlib.reload(module)

            PLUGIN_MTIMES[module_name] = mtime

    # -------------------------
    # Remove Deleted Plugins
    # -------------------------

    for module_name in list(PLUGIN_MODULES.keys()):

        file_name = module_name.split(".")[-1] + ".py"

        if file_name not in current_files:

            del sys.modules[module_name]
            del PLUGIN_MODULES[module_name]
            del PLUGIN_MTIMES[module_name]


# -------------------------
# Load Plugins (Initial + Hot Reload)
# -------------------------

def load_plugins():

    scan_plugins(force=True)

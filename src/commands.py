##############################

import importlib
import os
import time
import hashlib

COMMANDS = {}
BOT_INSTANCE = None

# -------------------------
# Admin Settings
# -------------------------

ADMIN_ADDRESSES = {"PUT_LXMF_ADDRESS_HERE"}

ADMIN_PASSWORD_HASH = hashlib.sha256(
    "changeme".encode()
).hexdigest()

ACTIVE_ADMINS = {}
LOGIN_COOLDOWN = {}

# -------------------------
# Cooldown Settings
# -------------------------

USER_LAST_COMMAND = {}
GLOBAL_COOLDOWN_SECONDS = 5
HELP_PAGE_SIZE = 5


# -------------------------
# Bot Reference
# -------------------------

def set_bot(bot):
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# -------------------------
# Register Command (WITH ALIASES)
# -------------------------

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
# Help Menu
# -------------------------

def help_menu(page=1):

    grouped = {}

    for cmd, entry in COMMANDS.items():
        if isinstance(entry, dict):
            category = entry.get("category", "general")
            grouped.setdefault(category, []).append((cmd, entry))

    categories = sorted(grouped.keys())
    total_pages = max(1, (len(categories) + HELP_PAGE_SIZE - 1) // HELP_PAGE_SIZE)

    if page < 1 or page > total_pages:
        return f"Invalid page. Use 1-{total_pages}", True

    start = (page - 1) * HELP_PAGE_SIZE
    end = start + HELP_PAGE_SIZE
    page_categories = categories[start:end]

    output = [f"📖 HELP (Page {page}/{total_pages})\n"]

    for category in page_categories:
        output.append(f"📦 {category.upper()}")

    output.append("\nUse:")
    output.append("• help")
    output.append("• help <page>")
    output.append("• help <category>")

    output.append("\n\nhttps://github.com/JamesM92/LXMF_Bot")
    return "\n".join(output), True


# -------------------------
# Category Help
# -------------------------

def category_help(category_name):

    category_name = category_name.lower()

    matches = [
        (cmd, entry)
        for cmd, entry in COMMANDS.items()
        if isinstance(entry, dict)
        and entry.get("category", "general").lower() == category_name
    ]

    if not matches:
        return "Category not found.", True

    output = [f"📦 {category_name.upper()}\n"]

    for cmd, entry in sorted(matches):
        admin_flag = " (admin)" if entry.get("admin") else ""
        output.append(f"• {cmd}{admin_flag} - {entry['desc']}")

    return "\n".join(output), True


# -------------------------
# Handle Commands
# -------------------------

def handle_command(message, sender):

    parts = message.strip().split()

    if not parts:
        return help_menu(1)

    raw_cmd = parts[0].lower()
    args = parts[1:]

    # Resolve alias
    cmd = raw_cmd
    if cmd in COMMANDS and isinstance(COMMANDS[cmd], str):
        cmd = COMMANDS[cmd]

    # HELP
    if cmd == "help":

        if not args:
            return help_menu(1)

        if args[0].isdigit():
            return help_menu(int(args[0]))

        return category_help(args[0])

    if cmd not in COMMANDS:
        return None, False

    entry = COMMANDS[cmd]

    if entry["admin"] and not is_admin(sender):
        return "Admin only.", True

    now = time.time()

    user_data = USER_LAST_COMMAND.get(sender, {})
    last_used = user_data.get(cmd, 0)

    # Per-command cooldown
    if now - last_used < entry["cooldown"]:
        remaining = int(entry["cooldown"] - (now - last_used))
        return f"Command cooldown. Try again in {remaining}s.", True

    # Global cooldown only when switching commands
    previous_command = user_data.get("last_command")

    if previous_command and previous_command != cmd:
        global_last = user_data.get("global_time", 0)

        if now - global_last < GLOBAL_COOLDOWN_SECONDS:
            remaining = int(GLOBAL_COOLDOWN_SECONDS - (now - global_last))
            return f"Global cooldown. Try again in {remaining}s.", True

    try:
        result = entry["func"](args + [sender])

        USER_LAST_COMMAND.setdefault(sender, {})
        USER_LAST_COMMAND[sender][cmd] = now
        USER_LAST_COMMAND[sender]["last_command"] = cmd
        USER_LAST_COMMAND[sender]["global_time"] = now

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

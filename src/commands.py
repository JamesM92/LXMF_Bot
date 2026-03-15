import importlib
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
# Snapshot (SAFE – no circular dependency)
# =====================================================

def get_commands_snapshot():

    snapshot = {}

    for name, entry in COMMANDS.items():
        if isinstance(entry, dict):
            snapshot[name] = entry

    return snapshot

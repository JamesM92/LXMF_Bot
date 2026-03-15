import os
import importlib

COMMANDS = {}


class Command:
    def __init__(self, name, function, description):
        self.name = name
        self.function = function
        self.description = description


def register(name, description):
    def wrapper(func):
        COMMANDS[name] = Command(name, func, description)
        return func
    return wrapper


def load_plugins():

    plugin_dir = "plugins"

    if not os.path.isdir(plugin_dir):
        return

    for file in os.listdir(plugin_dir):

        if file.endswith(".py") and file != "__init__.py":

            module_name = f"plugins.{file[:-3]}"
            importlib.import_module(module_name)


def handle_command(message, sender=None):

    parts = message.strip().split()

    if len(parts) == 0:
        return help_menu(), False

    cmd = parts[0].lower()
    args = parts[1:]

    if sender:
        args.append(sender)

    if cmd in COMMANDS:

        try:
            return COMMANDS[cmd].function(args), True
        except Exception:
            return "Command error.", True

    return help_menu(), False


def help_menu():

    output = ["Available Commands:\n"]

    for name in sorted(COMMANDS):
        output.append(f"{name} - {COMMANDS[name].description}")

    return "\n".join(output)


# load plugins automatically
load_plugins()

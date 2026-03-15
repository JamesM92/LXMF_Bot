import math
from commands import register, get_commands_snapshot

PAGE_SIZE = 5


def build_categories(commands):

    grouped = {}

    for name, data in commands.items():
        grouped.setdefault(data["category"], []).append(name)

    lines = ["📖 COMMAND CATEGORIES\n"]

    for category in sorted(grouped):
        lines.append(f"📦 {category}")

    lines.append("\nUse: help <category>")
    return "\n".join(lines)


@register(
    "help",
    "Show help menu",
    category="core",
    cooldown=5,
    aliases=["?", "h"]
)
def help_cmd(args):

    commands = get_commands_snapshot()

    if not args:
        return build_categories(commands)

    category = args[0].lower()

    filtered = [
        (name, data)
        for name, data in commands.items()
        if data["category"].lower() == category
    ]

    if not filtered:
        return f"No commands in '{category}'."

    lines = [f"📂 {category}\n"]

    for name, data in filtered[:PAGE_SIZE]:
        admin_flag = " (admin)" if data["admin"] else ""
        lines.append(f"• {name}{admin_flag} - {data['desc']}")

    return "\n".join(lines)

import math
from commands import register, get_commands_snapshot

PAGE_SIZE = 10


def build_category_view(commands):

    grouped = {}

    for name, data in commands.items():
        grouped.setdefault(data["category"], []).append(name)

    output = ["📖 COMMAND CATEGORIES\n"]

    for category in sorted(grouped):
        output.append(
            f"📦 {category} ({len(grouped[category])})"
        )

    output.append("\nUse: help <category>")
    return "\n".join(output)


@register(
    "help",
    "Show help menu",
    category="core",
    aliases=["?", "h"],
    cooldown=5
)
def help_cmd(args):

    commands = get_commands_snapshot()

    if not args:
        return build_category_view(commands)

    category = args[0]

    filtered = [
        (name, data)
        for name, data in commands.items()
        if data["category"].lower() == category.lower()
    ]

    if not filtered:
        return f"No commands in '{category}'."

    total_pages = math.ceil(len(filtered) / PAGE_SIZE)

    lines = [
        f"📂 {category}",
        f"Total Pages: {total_pages}\n"
    ]

    for name, data in filtered[:PAGE_SIZE]:

        admin_flag = " (admin)" if data["admin"] else ""
        lines.append(
            f"• {name}{admin_flag} - {data['desc']}"
        )

    return "\n".join(lines)

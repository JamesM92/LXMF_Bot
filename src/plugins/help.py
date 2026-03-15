import math
from commands import register, get_commands_snapshot


PAGE_SIZE = 5


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


def build_category_page(commands, category):

    filtered = [
        (name, data)
        for name, data in commands.items()
        if data["category"].lower() == category.lower()
    ]

    if not filtered:
        return f"No commands in '{category}'."

    total_pages = math.ceil(len(filtered) / PAGE_SIZE)

    pages = []

    for page in range(total_pages):

        start = page * PAGE_SIZE
        end = start + PAGE_SIZE

        chunk = filtered[start:end]

        lines = [
            f"📂 {category}",
            f"Page {page+1}/{total_pages}\n"
        ]

        for name, data in chunk:
            admin_flag = " (admin)" if data["admin"] else ""
            lines.append(
                f"• {name}{admin_flag} - {data['desc']}"
            )

        pages.append("\n".join(lines))

    return pages[0]


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

    return build_category_page(commands, args[0])

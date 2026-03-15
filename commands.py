def handle_command(command):

    command = command.lower().strip()

    commands = {
        "weather": weather,
        "help": help_menu,
        "?": help_menu,
    }

    if command in commands:
        return commands[command](), True
    else:
        return help_menu(), False


def help_menu():

    return (
        "Available Commands:\n"
        "weather - show temperature\n"
        "help - show this menu\n"
        "? - show this menu"
    )


def weather():

    return "Current temperature: 22°C"

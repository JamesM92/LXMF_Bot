import os
import time
import RNS

from LXMF import LXMRouter, LXMessage
from appdirs import AppDirs
from queue import Queue

import commands


class LXMFBot:

    def __init__(self, name="CommunityNode"):

        self.name = name
        self.queue = Queue()

        dirs = AppDirs("LXMFBot", "community")
        self.base_path = os.path.join(dirs.user_data_dir, name)
        os.makedirs(self.base_path, exist_ok=True)

        RNS.Reticulum(loglevel=RNS.LOG_INFO)

        idfile = os.path.join(self.base_path, "identity")

        if not os.path.isfile(idfile):
            identity = RNS.Identity(True)
            identity.to_file(idfile)

        self.id = RNS.Identity.from_file(idfile)

        self.router = LXMRouter(
            identity=self.id,
            storagepath=dirs.user_data_dir
        )

        self.local = self.router.register_delivery_identity(
            self.id,
            display_name=name
        )

        self.router.register_delivery_callback(
            self._message_received
        )

        self.state = {
            "cooldowns": {}
        }

        commands.set_bot(self)
        commands.load_plugins()

        print("🌐 Community Mesh Node Online")

    # =====================================================
    # MESSAGE HANDLER
    # =====================================================

    def _message_received(self, message):

        commands.scan_plugins()

        sender = RNS.hexrep(
            message.source_hash,
            delimit=False
        )

        content = message.content.decode("utf-8").strip()

        if not content:
            return

        def reply(msg):
            self.send(sender, str(msg))

        # Admin bypass handled inside commands

        # =====================================================
        # COOLDOWN SYSTEM
        # =====================================================

        if not commands.is_admin(sender):

            GLOBAL_COOLDOWN = 60
            parts = content.split()
            cmd_name = parts[0].lower()
            now = time.time()

            if sender not in self.state["cooldowns"]:
                self.state["cooldowns"][sender] = {
                    "last_global": 0,
                    "last_command": {},
                    "first_use": {}
                }

            user_data = self.state["cooldowns"][sender]

            command_entry = commands.COMMANDS.get(cmd_name)
            if isinstance(command_entry, str):
                cmd_name = command_entry
                command_entry = commands.COMMANDS.get(cmd_name)

            if command_entry:

                command_cooldown = command_entry.get("cooldown", 60)

                is_first_use = not user_data["first_use"].get(cmd_name, False)

                if is_first_use:

                    effective = (
                        command_cooldown
                        if command_cooldown < GLOBAL_COOLDOWN
                        else GLOBAL_COOLDOWN
                    )

                    remaining = effective - (now - user_data["last_global"])

                    if remaining > 0:
                        reply(f"⏳ Please wait {int(remaining)}s.")
                        return

                    user_data["first_use"][cmd_name] = True

                else:

                    remaining = command_cooldown - (
                        now - user_data["last_command"].get(cmd_name, 0)
                    )

                    if remaining > 0:
                        reply(f"⏳ Please wait {int(remaining)}s.")
                        return

                user_data["last_global"] = now
                user_data["last_command"][cmd_name] = now

        # =====================================================
        # EXECUTE COMMAND
        # =====================================================

        response, handled = commands.handle_command(
            content,
            sender
        )

        if handled and response is not None:
            reply(response)

    # =====================================================
    # SEND
    # =====================================================

    def send(self, destination, message):

        try:
            hash_bytes = bytes.fromhex(destination)
        except:
            return

        identity = RNS.Identity.recall(hash_bytes)

        if not identity:
            RNS.Transport.request_path(hash_bytes)
            return

        dest = RNS.Destination(
            identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "lxmf",
            "delivery"
        )

        lxm = LXMessage(
            dest,
            self.local,
            str(message),
            desired_method=LXMessage.DIRECT
        )

        self.queue.put(lxm)

    # =====================================================
    # RUN LOOP
    # =====================================================

    def run(self):

        while True:

            commands.scan_plugins()

            while not self.queue.empty():
                lxm = self.queue.get()
                self.router.handle_outbound(lxm)

            time.sleep(2)

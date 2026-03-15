#################################

import os
import time
import json
import RNS

from LXMF import LXMRouter, LXMessage
from appdirs import AppDirs
from queue import Queue

import commands


class LXMFBot:

    def __init__(self, name="CommunityNode"):

        self.name = name
        self.queue = Queue()
        self.cooldown_data = {}

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

        commands.set_bot(self)
        commands.load_plugins()

        print("🌐 Community Mesh Node Online")

    # -------------------------
    # Message Handling
    # -------------------------

    def _message_received(self, message):

        sender = RNS.hexrep(
            message.source_hash,
            delimit=False
        )

        content = message.content.decode("utf-8").strip()

        def reply(msg):
            self.send(sender, str(msg))

        if not content:
            return

        if commands.is_admin(sender):

            response, _ = commands.handle_command(
                content, sender
            )

            if response is not None:
                reply(response)

            return

        cmd = content.split()[0].lower()
        now = time.time()

        if sender not in self.cooldown_data:
            self.cooldown_data[sender] = {
                "last_command_time": 0,
                "commands": {},
                "warnings": {},
                "last_invalid_time": 0,
                "last_invalid_warning": 0
            }

        user_data = self.cooldown_data[sender]

        command_entry = commands.COMMANDS.get(cmd)

        # =====================================================
        # UNRECOGNIZED COMMAND LOGIC
        # =====================================================

        if not command_entry:

            ONE_HOUR = 3600
            ONE_MINUTE = 60

            # 1-minute warning cooldown
            if now - user_data["last_invalid_warning"] < ONE_MINUTE:
                return

            user_data["last_invalid_warning"] = now

            # Within 1-hour window → warning only
            if now - user_data["last_invalid_time"] < ONE_HOUR:

                reply("❌ Unrecognized command.")
                return

            # First time / expired → show help
            user_data["last_invalid_time"] = now

            reply(
                "❌ Unrecognized command.\n\n"
                + commands.help_menu()
            )

            return

        # =====================================================
        # VALID COMMAND COOLDOWNS
        # =====================================================

        GLOBAL_COOLDOWN = 60
        command_cooldown = command_entry.get("cooldown", 60)

        effective_cooldown = max(
            GLOBAL_COOLDOWN,
            command_cooldown
        )

        last_used = max(
            user_data["last_command_time"],
            user_data["commands"].get(cmd, 0)
        )

        if now - last_used < effective_cooldown:

            if not user_data["warnings"].get(cmd, False):

                remaining = int(
                    effective_cooldown - (now - last_used)
                )

                reply(f"⏳ Please wait {remaining}s.")

                user_data["warnings"][cmd] = True

            return

        user_data["commands"][cmd] = now
        user_data["last_command_time"] = now
        user_data["warnings"][cmd] = False

        response, _ = commands.handle_command(
            content, sender
        )

        if response is not None:
            reply(response)

    # -------------------------
    # Send
    # -------------------------

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

    # -------------------------
    # Run Loop
    # -------------------------

    def run(self):

        while True:
            while not self.queue.empty():
                lxm = self.queue.get()
                self.router.handle_outbound(lxm)

            time.sleep(2)

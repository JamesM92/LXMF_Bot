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

        self.reticulum = RNS.Reticulum(loglevel=RNS.LOG_INFO)

        try:
            RNS.Transport.start()
        except Exception:
            pass

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
            self.send(sender, msg)

        if not content:
            return

        # Admin bypass
        if commands.is_admin(sender):

            response, _ = commands.handle_command(
                content, sender
            )

            if response is not None:
                reply(str(response))

            return

        cmd = content.split()[0].lower()

        now = time.time()

        if sender not in self.cooldown_data:
            self.cooldown_data[sender] = {
                "last_command_time": 0,
                "commands": {},
                "warnings": {},
                "last_invalid_time": 0
            }

        user_data = self.cooldown_data[sender]

        command_entry = commands.COMMANDS.get(cmd)

        # -------------------------
        # Unrecognized Command Cooldown
        # -------------------------

        if not command_entry:

            UNRECOGNIZED_COOLDOWN = 30

            if now - user_data["last_invalid_time"] < UNRECOGNIZED_COOLDOWN:

                if not user_data["warnings"].get("_invalid", False):

                    remaining = int(
                        UNRECOGNIZED_COOLDOWN -
                        (now - user_data["last_invalid_time"])
                    )

                    reply(
                        f"❌ Unrecognized command. "
                        f"Try again in {remaining}s.\n\n"
                        + commands.help_menu()
                    )

                    user_data["warnings"]["_invalid"] = True

                return

            user_data["last_invalid_time"] = now
            user_data["warnings"]["_invalid"] = False

            reply(
                "❌ Unrecognized command.\n\n"
                + commands.help_menu()
            )

            return

        # -------------------------
        # Valid Command Cooldowns
        # -------------------------

        GLOBAL_COOLDOWN = 60
        command_cooldown = command_entry.get("cooldown", 60)

        effective_cooldown = max(
            GLOBAL_COOLDOWN,
            command_cooldown
        )

        last_used_global = user_data["last_command_time"]
        last_used_cmd = user_data["commands"].get(cmd, 0)

        last_used = max(last_used_global, last_used_cmd)

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
            reply(str(response))

    # -------------------------
    # Send Message
    # -------------------------

    def send(self, destination, message):

        message = str(message)

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
            message,
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

            time.sleep(2)#################################

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

        # Reticulum
        self.reticulum = RNS.Reticulum(loglevel=RNS.LOG_INFO)

        try:
            RNS.Transport.start()
        except Exception:
            pass

        # Identity
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

        content = message.content.decode(
            "utf-8"
        ).strip()

        def reply(msg):
            self.send(sender, msg)

        # Admin bypass cooldown
        if commands.is_admin(sender):

            response, _ = commands.handle_command(
                content, sender
            )

            if response is not None:
                reply(str(response))

            return

        # -------------------------
        # Cooldowns
        # -------------------------

        cmd = content.split()[0].lower() if content else ""
        if not cmd:
            return

        command_entry = commands.COMMANDS.get(cmd)

        if not command_entry:
            response, _ = commands.handle_command(
                content, sender
            )
            if response:
                reply(str(response))
            return

        now = time.time()

        GLOBAL_COOLDOWN = 60
        command_cooldown = command_entry.get(
            "cooldown", 60
        )

        effective_cooldown = max(
            GLOBAL_COOLDOWN,
            command_cooldown
        )

        if sender not in self.cooldown_data:
            self.cooldown_data[sender] = {
                "last_command_time": 0,
                "commands": {},
                "warnings": {}
            }

        user_data = self.cooldown_data[sender]

        last_used_global = user_data["last_command_time"]
        last_used_cmd = user_data["commands"].get(cmd, 0)

        last_used = max(
            last_used_global,
            last_used_cmd
        )

        if now - last_used < effective_cooldown:

            if not user_data["warnings"].get(cmd, False):

                remaining = int(
                    effective_cooldown - (now - last_used)
                )

                reply(
                    f"⏳ Please wait {remaining}s."
                )

                user_data["warnings"][cmd] = True

            return

        # Passed cooldown
        user_data["commands"][cmd] = now
        user_data["last_command_time"] = now
        user_data["warnings"][cmd] = False

        self.cooldown_data[sender] = user_data

        response, _ = commands.handle_command(
            content, sender
        )

        if response is not None:
            reply(str(response))

    # -------------------------
    # Send Message
    # -------------------------

    def send(self, destination, message):

        message = str(message)

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
            message,
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

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

        self.router.register_delivery_callback(self._message_received)

        commands.set_bot(self)
        commands.load_plugins()

        print("🌐 Community Mesh Node Online")

    # -------------------------
    # Message Handling
    # -------------------------

    def _message_received(self, message):

        sender = RNS.hexrep(message.source_hash, delimit=False)
        content = message.content.decode("utf-8").strip()

        def reply(msg):
            self.send(sender, msg)

        # Admin bypass cooldowns
        if commands.is_admin(sender):
            response, _ = commands.handle_command(content, sender)
            if response is not None:
                reply(str(response))
            return

        # -------------------------
        # Per-Command Cooldown
        # -------------------------

        cmd = content.split()[0].lower() if content else ""
        if not cmd:
            return

        command_entry = commands.COMMANDS.get(cmd)
        if not command_entry:
            return

        cooldown = command_entry.get("cooldown", 60)
        now = time.time()

        if sender not in self.cooldown_data:
            self.cooldown_data[sender] = {"commands": {}, "warnings": {}}

        user_data = self.cooldown_data[sender]

        last_used = user_data["commands"].get(cmd, 0)

        if now - last_used < cooldown:

            if not user_data["warnings"].get(cmd, False):

                remaining = int(cooldown - (now - last_used))
                reply(f"⏳ Command on cooldown. Try again in {remaining}s.")
                user_data["warnings"][cmd] = True

            return

        # Reset warning + update timestamp
        user_data["commands"][cmd] = now
        user_data["warnings"][cmd] = False

        # Execute command
        response, _ = commands.handle_command(content, sender)

        if response is not None:
            reply(str(response))

    # -------------------------
    # LXMF Safe Send
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

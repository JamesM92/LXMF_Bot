#################################
# lxmfbot.py
#################################

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

        # Per-user per-command cooldown storage
        self.cooldowns = {}

        # Stats storage
        self.state = {
            "stats": {
                "total": 0,
                "per_user": {},
                "per_command": {}
            }
        }

        # -------------------------
        # Identity Setup
        # -------------------------

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

        # Link bot to command system
        commands.set_bot(self)
        commands.load_plugins()

        print("🌐 Community Mesh Node Online")

    # =====================================================
    # Message Handling
    # =====================================================

    def _message_received(self, message):

        sender = RNS.hexrep(
            message.source_hash,
            delimit=False
        )

        content = message.content.decode("utf-8").strip()

        if not content:
            return

        cmd_name = content.split()[0].lower()

        # Execute command
        response, handled = commands.handle_command(content, sender)

        if not handled:
            self.send(sender, "❌ Unrecognized command.")
            return

        # Resolve alias to real command entry
        entry = commands.COMMANDS.get(cmd_name)
        if isinstance(entry, str):
            entry = commands.COMMANDS.get(entry)

        # =====================================================
        # 🚀 ADMIN BYPASS (ABSOLUTE PRIORITY)
        # =====================================================

        if commands.is_admin(sender):

            self._update_stats(sender, cmd_name)

            if response is not None:
                self.send(sender, str(response))

            return

        # =====================================================
        # NORMAL COOLDOWN FLOW
        # =====================================================

        if not self._check_cooldown(sender, cmd_name, entry):
            return

        self._update_stats(sender, cmd_name)

        if response is not None:
            self.send(sender, str(response))

    # =====================================================
    # Cooldown Logic
    # =====================================================

    def _check_cooldown(self, sender, cmd, entry):

        now = time.time()

        if sender not in self.cooldowns:
            self.cooldowns[sender] = {}

        user_data = self.cooldowns[sender]

        command_cooldown = entry.get("cooldown", 60) if entry else 60

        last_used = user_data.get(cmd)

        # -------------------------------------------------
        # FIRST TIME USING THIS COMMAND
        # -------------------------------------------------
        if last_used is None:
            # Allow immediate execution
            user_data[cmd] = now
            return True

        # -------------------------------------------------
        # NORMAL COOLDOWN CHECK
        # -------------------------------------------------
        elapsed = now - last_used

        if elapsed < command_cooldown:

            remaining = int(command_cooldown - elapsed)

            self.send(
                sender,
                f"⏳ Please wait {remaining}s before using '{cmd}' again."
            )

            return False

        # Update timestamp
        user_data[cmd] = now
        return True

    # =====================================================
    # Stats
    # =====================================================

    def _update_stats(self, sender, cmd):

        stats = self.state["stats"]

        stats["total"] += 1
        stats["per_user"][sender] = stats["per_user"].get(sender, 0) + 1
        stats["per_command"][cmd] = stats["per_command"].get(cmd, 0) + 1

    # =====================================================
    # Send Message
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
    # Run Loop
    # =====================================================

    def run(self):

        while True:
            while not self.queue.empty():
                lxm = self.queue.get()
                self.router.handle_outbound(lxm)

            time.sleep(2)

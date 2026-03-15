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

        # -------------------------
        # Bot State
        # -------------------------

        self.state = {
            "lockdown": False,
            "stats": {
                "total": 0,
                "per_user": {},
                "per_command": {}
            }
        }

        commands.set_bot(self)
        commands.load_plugins()

        print("🌐 Community Mesh Node Online")

    # -------------------------
    # Lockdown Toggle
    # -------------------------

    def toggle_lockdown(self):

        self.state["lockdown"] = not self.state["lockdown"]
        return self.state["lockdown"]

    # -------------------------
    # Message Handling
    # -------------------------

    def _message_received(self, message):

        sender = RNS.hexrep(
            message.source_hash,
            delimit=False
        )

        content = message.content.decode("utf-8").strip()

        if not content:
            return

        # Optional: Lockdown enforcement
        if self.state["lockdown"] and not commands.is_admin(sender):
            return

        def reply(msg):
            self.send(sender, str(msg))

        response, handled = commands.handle_command(
            content,
            sender
        )

        if handled:

            # -------------------------
            # Update Stats
            # -------------------------

            stats = self.state["stats"]
            stats["total"] += 1

            stats["per_user"][sender] = \
                stats["per_user"].get(sender, 0) + 1

            cmd_name = content.split()[0].lower()

            stats["per_command"][cmd_name] = \
                stats["per_command"].get(cmd_name, 0) + 1

            if response is not None:
                reply(response)

        else:
            reply(
                "❌ Unrecognized command.\n\n"
                + commands.help_menu()[0]
            )

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

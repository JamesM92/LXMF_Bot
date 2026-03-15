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

        # -------------------------
        # Reticulum Initialization
        # -------------------------

        self.reticulum = RNS.Reticulum(loglevel=RNS.LOG_INFO)

        try:
            RNS.Transport.start()
        except Exception:
            pass

        # -------------------------
        # Identity
        # -------------------------

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

        # -------------------------
        # Load Commands + Plugins HERE
        # -------------------------

        commands.set_bot(self)
        commands.load_plugins()

        # -------------------------
        # Persistent State
        # -------------------------

        self.state_file = os.path.join(self.base_path, "state.json")
        self._load_state()

        print("🌐 Community Mesh Node Online")

    # -------------------------
    # State Handling
    # -------------------------

    def _load_state(self):

        self.state = {
            "lockdown": False,
            "command_log": [],
            "stats": {
                "total": 0,
                "per_user": {},
                "per_command": {}
            },
            "network_rate": []
        }

        try:
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
        except:
            pass

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f)

    # -------------------------
    # Message Handling
    # -------------------------

    def _message_received(self, message):

        sender = RNS.hexrep(message.source_hash, delimit=False)
        content = message.content.decode("utf-8").strip()
        now = time.time()

        def reply(msg):
            self.send(sender, msg)

        # Rate limit
        self.state["network_rate"] = [
            t for t in self.state["network_rate"]
            if now - t < 60
        ]

        if len(self.state["network_rate"]) >= 30:
            if not commands.is_admin(sender):
                reply("Network busy.")
                return

        self.state["network_rate"].append(now)

        # Lockdown
        if self.state.get("lockdown", False):
            if not commands.is_admin(sender):
                reply("🔒 Node is in LOCKDOWN mode.")
                return

        response, _ = commands.handle_command(content, sender)

        if response:
            reply(response)

        self._log(sender, content)
        self._save_state()

    # -------------------------
    # Logging
    # -------------------------

    def _log(self, sender, cmd):

        stats = self.state["stats"]

        stats["total"] += 1
        stats["per_user"].setdefault(sender, 0)
        stats["per_user"][sender] += 1
        stats["per_command"].setdefault(cmd, 0)
        stats["per_command"][cmd] += 1

    # -------------------------
    # Sending
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

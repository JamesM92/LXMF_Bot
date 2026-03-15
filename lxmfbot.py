import os
import time
import json
import RNS

from LXMF import LXMRouter, LXMessage
from appdirs import AppDirs
from queue import Queue
from types import SimpleNamespace

import commands


class LXMFBot:

    def __init__(self, name="LXMFBot", announce=360):

        self.name = name
        self.cooldown_data = {}

        dirs = AppDirs("LXMFBot", "community")
        self.base_path = os.path.join(dirs.user_data_dir, name)

        os.makedirs(self.base_path, exist_ok=True)

        # Identity
        idfile = os.path.join(self.base_path, "identity")
        if not os.path.isfile(idfile):
            identity = RNS.Identity(True)
            identity.to_file(idfile)

        self.id = RNS.Identity.from_file(idfile)

        RNS.Reticulum(loglevel=RNS.LOG_INFO)

        self.router = LXMRouter(identity=self.id, storagepath=dirs.user_data_dir)
        self.local = self.router.register_delivery_identity(
            self.id, display_name=name
        )

        self.router.register_delivery_callback(self._message_received)

        # Global state
        self.state_file = os.path.join(self.base_path, "state.json")
        self._load_state()

        self.queue = Queue()

        print("Community Mesh Node Ready.")

    # -------------------------
    # State Handling
    # -------------------------

    def _load_state(self):
        self.state = {
            "lockdown": False,
            "command_log": [],
            "stats": {"total": 0, "per_user": {}, "per_command": {}},
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

        # Duplicate protection handled by LXMF internally

        # -------------------------
        # Network-wide rate limit
        # -------------------------

        self.state["network_rate"] = [
            t for t in self.state["network_rate"]
            if now - t < 60
        ]

        if len(self.state["network_rate"]) >= 30:
            if not commands.is_admin(sender):
                reply("Network busy. Try again shortly.")
                return

        self.state["network_rate"].append(now)

        # -------------------------
        # Lockdown Mode
        # -------------------------

        if self.state.get("lockdown", False):
            if not commands.is_admin(sender):
                reply("Node is in LOCKDOWN mode.")
                return

        # -------------------------
        # Admin Bypass Cooldowns
        # -------------------------

        if commands.is_admin(sender):
            response, known = commands.handle_command(content, sender)

            if response:
                reply(response)

            self._log_command(sender, content)
            self._save_state()
            return

        # -------------------------
        # Cooldown System
        # -------------------------

        cmd = content.split()[0].lower() if content else ""

        user = self.cooldown_data.get(sender, {})

        last_times = user.get("commands", {})

        last_used = last_times.get(cmd, 0)

        now = time.time()

        same_cd = 300
        diff_cd = 60

        time_since = now - last_used

        if time_since < same_cd if cmd in last_times else time_since < diff_cd:

            reply("Cooldown active. Please wait.")
            return

        response, known = commands.handle_command(content, sender)

        if response:
            reply(response)

        # Update cooldown tracking
        if sender not in self.cooldown_data:
            self.cooldown_data[sender] = {"commands": {}}

        self.cooldown_data[sender]["commands"][cmd] = now

        self._log_command(sender, cmd)

        self._save_state()

    # -------------------------
    # Logging & Stats
    # -------------------------

    def _log_command(self, sender, cmd):

        now = time.time()

        self.state["stats"]["total"] += 1
        self.state["stats"]["per_user"].setdefault(sender, 0)
        self.state["stats"]["per_user"][sender] += 1

        self.state["stats"]["per_command"].setdefault(cmd, 0)
        self.state["stats"]["per_command"][cmd] += 1

        self.state["command_log"].append({
            "time": now,
            "sender": sender,
            "command": cmd
        })

        if len(self.state["command_log"]) > 1000:
            self.state["command_log"] = self.state["command_log"][-1000:]

    # -------------------------
    # Sending
    # -------------------------

    def send(self, destination, message):

        try:
            hash = bytes.fromhex(destination)
        except:
            return

        identity = RNS.Identity.recall(hash)

        if not identity:
            RNS.Transport.request_path(hash)
            return

        dest = RNS.Destination(
            identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "lxmf",
            "delivery",
        )

        lxm = LXMessage(
            dest,
            self.local,
            message,
            desired_method=LXMessage.DIRECT
        )

        self.queue.put(lxm)

    def run(self):

        while True:
            while not self.queue.empty():
                lxm = self.queue.get()
                self.router.handle_outbound(lxm)

            time.sleep(5)

import os
import time
import RNS

from LXMF import LXMRouter, LXMessage
from appdirs import AppDirs
from queue import Queue
from types import SimpleNamespace

import commands


class LXMFBot:

    delivery_callbacks = []
    receipts = []
    queue = Queue(maxsize=5)

    def __init__(self, name="LXMFBot", announce=360, announce_immediately=False):

        self.name = name
        self.announce_time = announce

        # cooldown system
        self.cooldown = 300
        self.user_last_message = {}
        self.user_warned = {}
        self.user_exception_used = {}

        dirs = AppDirs("LXMFBot", "randogoth")
        self.config_path = os.path.join(dirs.user_data_dir, name)

        idfile = os.path.join(self.config_path, "identity")

        if not os.path.isdir(dirs.user_data_dir):
            os.mkdir(dirs.user_data_dir)

        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        if not os.path.isfile(idfile):
            RNS.log("No Primary Identity file found, creating new...", RNS.LOG_INFO)
            identity = RNS.Identity(True)
            identity.to_file(idfile)

        self.id = RNS.Identity.from_file(idfile)
        RNS.log("Loaded identity from file", RNS.LOG_INFO)

        if announce_immediately:
            af = os.path.join(self.config_path, "announce")
            if os.path.isfile(af):
                os.remove(af)
                RNS.log("Announcing now. Timer reset.", RNS.LOG_INFO)

        RNS.Reticulum(loglevel=RNS.LOG_VERBOSE)

        self.router = LXMRouter(identity=self.id, storagepath=dirs.user_data_dir)

        self.local = self.router.register_delivery_identity(
            self.id, display_name=name
        )

        self.router.register_delivery_callback(self._message_received)

        RNS.log(
            "LXMF Router ready to receive on: {}".format(
                RNS.prettyhexrep(self.local.hash)
            ),
            RNS.LOG_INFO,
        )

        self._announce()

    def _announce(self):

        announce_path = os.path.join(self.config_path, "announce")

        if os.path.isfile(announce_path):
            with open(announce_path, "r") as f:
                announce = int(f.readline())
        else:
            announce = 1

        if announce > int(time.time()):
            return

        with open(announce_path, "w+") as af:
            next_announce = int(time.time()) + self.announce_time
            af.write(str(next_announce))

        self.local.announce()

        RNS.log(
            f"Announcement sent, next in {self.announce_time} seconds",
            RNS.LOG_INFO,
        )

    def received(self, function):
        self.delivery_callbacks.append(function)
        return function

    def _message_received(self, message):

        sender = RNS.hexrep(message.source_hash, delimit=False)
        receipt = RNS.hexrep(message.hash, delimit=False)

        RNS.log(f"Message receipt <{receipt}>", RNS.LOG_INFO)

        def reply(msg):
            self.send(sender, msg)

        if receipt in self.receipts:
            return

        self.receipts.append(receipt)

        if len(self.receipts) > 100:
            self.receipts.pop(0)

        content = message.content.decode("utf-8").strip()

        obj = {
            "lxmf": message,
            "reply": reply,
            "sender": sender,
            "content": content,
            "hash": receipt,
        }

        msg = SimpleNamespace(**obj)

        for callback in self.delivery_callbacks:
            callback(msg)

        now = time.time()

        last = self.user_last_message.get(sender, 0)
        warned = self.user_warned.get(sender, False)
        exception_used = self.user_exception_used.get(sender, False)

        cooldown_active = (now - last) < self.cooldown

        command = content.lower().strip()

        try:
            response, known = commands.handle_command(command, sender)
        except Exception as e:
            RNS.log(f"Command handler error: {e}", RNS.LOG_ERROR)
            reply("Error processing command.")
            return

        is_help = command in ["help", "?"]
        is_unknown = not known

        exception_allowed = (is_help or is_unknown) and not exception_used

        if cooldown_active and not exception_allowed:

            if not warned:
                reply("Please wait 5 minutes before sending another command.")
                self.user_warned[sender] = True

            return

        if response:
            reply(response)

        self.user_last_message[sender] = now
        self.user_warned[sender] = False

        if exception_allowed:
            self.user_exception_used[sender] = True
        else:
            self.user_exception_used[sender] = False

    def send(self, destination, message, title="Reply"):

        try:
            hash = bytes.fromhex(destination)
        except Exception:
            RNS.log("Invalid destination hash", RNS.LOG_ERROR)
            return

        if not len(hash) == RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
            RNS.log("Invalid destination hash length", RNS.LOG_ERROR)
            return

        identity = RNS.Identity.recall(hash)

        if identity is None:

            RNS.log(
                "Identity unknown. Requesting network path.",
                RNS.LOG_ERROR,
            )

            RNS.Transport.request_path(hash)
            return

        lxmf_destination = RNS.Destination(
            identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "lxmf",
            "delivery",
        )

        lxm = LXMessage(
            lxmf_destination,
            self.local,
            message,
            title=title,
            desired_method=LXMessage.DIRECT,
        )

        lxm.try_propagation_on_fail = True

        self.queue.put(lxm)

    def run(self, delay=10):

        RNS.log(
            f"LXMF Bot `{self.name}` awaiting messages...",
            RNS.LOG_INFO,
        )

        while True:

            while not self.queue.empty():
                lxm = self.queue.get()
                self.router.handle_outbound(lxm)

            self._announce()

            time.sleep(delay)

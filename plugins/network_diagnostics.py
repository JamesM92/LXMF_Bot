##########################

import time
import RNS
from commands import register


@register("interfaces", "Show active Reticulum interfaces", "network")
def interfaces(args):

    try:
        interfaces = getattr(RNS.Transport, "interfaces", [])

        if not interfaces:
            return "No active interfaces found."

        return "Active Interfaces:\n" + "\n".join(f"- {i}" for i in interfaces)

    except Exception as e:
        return f"Error: {repr(e)}"


@register("neighbors", "Show known network neighbors", "network")
def neighbors(args):

    try:
        neighbors = getattr(
            RNS.Transport,
            "neighbours",
            getattr(RNS.Transport, "neighbors", [])
        )

        if not neighbors:
            return "No neighbors currently known."

        return "Known Neighbors:\n" + "\n".join(f"- {n}" for n in neighbors)

    except Exception as e:
        return f"Error: {repr(e)}"


@register("paths", "Show known destination paths", "network")
def paths(args):

    try:
        paths = getattr(RNS.Transport, "paths", [])

        if not paths:
            return "No known paths."

        return "Known Paths:\n" + "\n".join(f"- {p}" for p in paths)

    except Exception as e:
        return f"Error: {repr(e)}"


@register("nodeinfo", "Show Reticulum node information", "network")
def nodeinfo(args):

    try:
        interfaces = getattr(RNS.Transport, "interfaces", [])
        neighbors = getattr(
            RNS.Transport,
            "neighbours",
            getattr(RNS.Transport, "neighbors", [])
        )
        paths = getattr(RNS.Transport, "paths", [])

        info = [
            "Reticulum Node Information",
            "---------------------------",
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Interfaces: {len(interfaces)}",
            f"Neighbors: {len(neighbors)}",
            f"Known Paths: {len(paths)}"
        ]

        return "\n".join(info)

    except Exception as e:
        return f"Error: {repr(e)}"


@register("announce", "Manually trigger LXMF announce", "network", admin=True)
def announce(args):

    try:
        RNS.Transport.announce()
        return "Announcement sent."
    except Exception as e:
        return f"Failed to send announce: {repr(e)}"

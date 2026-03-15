import time
import RNS

from commands import register


@register("interfaces", "Show active Reticulum interfaces", "network")
def interfaces(args):

    try:
        interfaces = RNS.Transport.interfaces

        if not interfaces:
            return "No active interfaces found."

        output = ["Active Interfaces:"]

        for i in interfaces:
            output.append(f"- {i}")

        return "\n".join(output)

    except Exception:
        return "Unable to retrieve interfaces."


@register("neighbors", "Show known network neighbors", "network")
def neighbors(args):

    try:
        neighbors = RNS.Transport.neighbours

        if not neighbors:
            return "No neighbors currently known."

        output = ["Known Neighbors:"]

        for n in neighbors:
            output.append(f"- {n}")

        return "\n".join(output)

    except Exception:
        return "Unable to retrieve neighbors."


@register("paths", "Show known destination paths", "network")
def paths(args):

    try:
        paths = RNS.Transport.paths

        if not paths:
            return "No known paths."

        output = ["Known Paths:"]

        for p in paths:
            output.append(f"- {p}")

        return "\n".join(output)

    except Exception:
        return "Unable to retrieve paths."


@register("nodeinfo", "Show Reticulum node information", "network")
def nodeinfo(args):

    try:
        info = []

        info.append("Reticulum Node Information")
        info.append("---------------------------")

        info.append(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        info.append(f"Interfaces: {len(RNS.Transport.interfaces)}")
        info.append(f"Neighbors: {len(RNS.Transport.neighbours)}")
        info.append(f"Known Paths: {len(RNS.Transport.paths)}")

        return "\n".join(info)

    except Exception:
        return "Unable to retrieve node information."


@register("announce", "Manually trigger LXMF announce", "network", admin=True)
def announce(args):

    try:
        RNS.Transport.announce()
        return "Announcement sent."

    except Exception:
        return "Failed to send announce."

import daemon

import gatekeeper

with daemon.DaemonContext():
    gk = gatekeeper.GateKeeper()
    gk.daemonize()

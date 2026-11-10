"""Background probes: ping, ss, tc sampling and tcpdump. Each returns (node, pid) to stop later."""
from traffic.iperf import bg


def ping(host, dst_ip, outfile, interval=0.2):
    """-D prefixes every reply with a Unix timestamp."""
    return host, bg(host, f'ping -D -i {interval} {dst_ip} > {outfile} 2>&1')


def ss_sampler(host, dst_ip, outfile, interval=0.1):
    """cwnd, RTT and pacing rate of every TCP socket from host to dst_ip."""
    loop = (f'while true; do echo "T $(date +%s.%N)"; ss -tin dst {dst_ip}; '
            f'sleep {interval}; done')
    return host, bg(host, f'({loop}) > {outfile} 2>&1')


def qdisc_sampler(node, intf, outfile, interval=0.5):
    """Backlog and drop counters of the bottleneck queue."""
    loop = (f'while true; do echo "T $(date +%s.%N)"; tc -s qdisc show dev {intf}; '
            f'sleep {interval}; done')
    return node, bg(node, f'({loop}) > {outfile} 2>&1')


def tcpdump(node, intf, outfile, snaplen=96):
    """Headers only. -U writes each packet as it arrives, so a stopped capture is complete.
    -Z root: Ubuntu's tcpdump otherwise drops to the 'tcpdump' user, which cannot write
    into the root-owned trial folder."""
    return node, bg(node, f'tcpdump -Z root -i {intf} -s {snaplen} -U -w {outfile} > /dev/null 2>&1')


def stop(probes):
    """SIGTERM lets tcpdump close its file cleanly; SIGKILL catches anything left."""
    for node, pid in probes:
        node.cmd(f'kill -TERM {pid} 2>/dev/null')
    for node, pid in probes:
        node.cmd(f'sleep 0.2; kill -9 {pid} 2>/dev/null')

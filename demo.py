"""Live demo for the presentation. Press Enter to advance each stage.

  sudo python3 -u demo.py

Every second it redraws one block: each flow's received rate as a bar, the bottleneck
queue's backlog, and the ping RTT across the bottleneck. The router's traffic is also
written to /tmp/demo.pcap for a live Wireshark view on the Mac (helpers/mac.zsh: livecap).
"""
import re
import time

from mininet.log import setLogLevel

from topo.dumbbell import IP, bottleneck, configure, start
from topo.shaping import apply_bottleneck
from traffic import probes
from traffic.iperf import bg

RATE, RTT = 50, 40
RATE_RE = re.compile(r'sec\s+[\d.]+ \w?Bytes\s+([\d.]+) ([KMG]?)bits/sec')
TO_MBPS = {'': 1e-6, 'K': 1e-3, 'M': 1.0, 'G': 1e3}
QUEUE_RE = re.compile(r'parent 1:10.*?backlog \S+ (\d+)p', re.S)   # the child queue, not htb
PING_RE = re.compile(r'time=([\d.]+) ms')
PCAP, PING_LOG = '/tmp/demo.pcap', '/tmp/demo_ping.log'
# The capture is taken after the queue, so drops never appear: losses show up as duplicate
# ACKs and as retransmissions Wireshark may label out-of-order.
LOSS_FILTER = 'tcp.analysis.duplicate_ack || tcp.analysis.retransmission || tcp.analysis.out_of_order'
BAR = 25                                    # characters for a full 50 Mbps bar
# label: (sender, receiver, port, iperf3 client options)
FLOWS = {'CUBIC h1': ('h1', 'h5', 5201, '-C cubic'),
         'BBR h2': ('h2', 'h6', 5202, '-C bbr'),
         'UDP h4': ('h4', 'h8', 5204, f'-u -b {RATE}M -l 1200')}


def stage(text):
    input(f'\n>>> {text}  [Enter]')


def last_match(path, regex):
    """Last match of regex in a log file, or None."""
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        m = regex.search(line)
        if m:
            return m
    return None


def received_mbps(label):
    """Latest 1-second rate the receiver saw, from its iperf3 server log."""
    m = last_match(f'/tmp/demo_{label.split()[1]}.log', RATE_RE)
    return float(m.group(1)) * TO_MBPS[m.group(2)] if m else None


def queue_pkts(tc_output):
    """Packets waiting in the bottleneck's child queue (pfifo or fq_codel)."""
    m = QUEUE_RE.search(tc_output)
    return int(m.group(1)) if m else None


def bar(mbps):
    n = round(min(mbps, RATE) / RATE * BAR)
    return '█' * n + '·' * (BAR - n)


def block(t, rates, queue, buf, rtt):
    lines = [f'  t={t:2d}s']
    lines += [f'  {label:9s} {bar(r)} {r:5.1f} Mbps' for label, r in rates.items()]
    lines.append(f'  {"total":9s} {" " * BAR} {sum(rates.values()):5.1f} Mbps')
    q = '?' if queue is None else queue
    ping = '?' if rtt is None else f'{rtt:.0f}'
    lines.append(f'  queue {q:>4}/{buf} pkts    ping RTT {ping:>4} ms (path {RTT} ms)')
    return lines


def watch(active, seconds, r1, bott, buf):
    """Redraw the status block in place once a second."""
    shown = 0
    for t in range(1, seconds + 1):
        time.sleep(1)
        rates = {label: received_mbps(label) or 0.0 for label in active}
        m = last_match(PING_LOG, PING_RE)
        lines = block(t, rates, queue_pkts(r1.cmd(f'tc -s qdisc show dev {bott}')), buf,
                      float(m.group(1)) if m else None)
        if shown:
            print(f'\033[{shown}A\r', end='')      # back to the top of the last block
        print('\n'.join(line + '\033[K' for line in lines), flush=True)
        shown = len(lines)


def main():
    setLogLevel('warning')
    net = start()
    running = []
    try:
        buf = configure(net, RATE, RTT, 1.0, 'pfifo')
        r1, bott = bottleneck(net)
        for label, (src, dst, port, _) in FLOWS.items():
            bg(net.get(dst), f'iperf3 -s -p {port} -i 1 --forceflush > /tmp/demo_{src}.log 2>&1')
        # A fresh, readable file before livecap's `tail -f` can open it.
        r1.cmd(f'rm -f {PCAP}; install -m 644 /dev/null {PCAP}')
        running.append(probes.ping(net.get('hp'), IP['hr'], PING_LOG))
        running.append(probes.tcpdump(r1, bott, PCAP))

        stage(f'1. Dumbbell is up: {RATE} Mbps bottleneck on {bott}, {RTT} ms RTT, '
              f'pfifo buffer of {buf} packets (1x BDP). On the Mac, run livecap now. '
              f'Show the tc config')
        print(r1.cmd(f'tc qdisc show dev {bott}'))
        active = []
        for step, label in [('2. Start one CUBIC flow', 'CUBIC h1'),
                            ('3. Add a BBR flow and watch the shares shift', 'BBR h2'),
                            ('4. Add UDP at 100% of the link and watch TCP collapse', 'UDP h4')]:
            stage(step)
            src, dst, port, opts = FLOWS[label]
            bg(net.get(src), f'iperf3 -c {IP[dst]} -p {port} -t 600 {opts} > /dev/null 2>&1')
            active.append(label)
            watch(active, 15, r1, bott, buf)
        stage('5. Switch the bottleneck queue to fq_codel and watch TCP recover')
        apply_bottleneck(r1, bott, RATE, buf, 'fq_codel')
        print(r1.cmd(f'tc qdisc show dev {bott}'))
        watch(active, 20, r1, bott, buf)
        stage(f'6. In Wireshark, filter {LOSS_FILTER}. Enter ends the demo')
    finally:
        # Ctrl+C inside node.cmd() leaves that node waiting, and its next cmd() would assert.
        for node in net.hosts:
            if node.waiting:
                node.waitOutput()
        try:
            probes.stop(running)
            for host in net.hosts:
                host.cmd('pkill -9 iperf3')
        finally:
            net.stop()


if __name__ == '__main__':
    main()

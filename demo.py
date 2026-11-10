"""Live demo for the presentation. Press Enter to advance each stage.

  sudo python3 -u demo.py
"""
import re
import time

from mininet.log import setLogLevel

from topo.dumbbell import IP, bottleneck, configure, start
from topo.shaping import apply_bottleneck
from traffic.iperf import bg

RATE, RTT = 50, 40
RATE_RE = re.compile(r'sec\s+[\d.]+ \w?Bytes\s+([\d.]+) ([KMG]?)bits/sec')
TO_MBPS = {'': 1e-6, 'K': 1e-3, 'M': 1.0, 'G': 1e3}
# label: (sender, receiver, port, iperf3 client options)
FLOWS = {'CUBIC h1': ('h1', 'h5', 5201, '-C cubic'),
         'BBR h2': ('h2', 'h6', 5202, '-C bbr'),
         'UDP h4': ('h4', 'h8', 5204, f'-u -b {RATE}M -l 1200')}


def stage(text):
    input(f'\n>>> {text}  [Enter]')


def received_mbps(label):
    """Latest 1-second rate the receiver saw, from its iperf3 server log."""
    try:
        lines = open(f'/tmp/demo_{label.split()[1]}.log').read().splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        m = RATE_RE.search(line)
        if m:
            return float(m.group(1)) * TO_MBPS[m.group(2)]
    return None


def watch(active, seconds):
    for t in range(1, seconds + 1):
        time.sleep(1)
        rates = {label: received_mbps(label) or 0.0 for label in active}
        cols = '   '.join(f'{label}: {rate:5.1f}' for label, rate in rates.items())
        print(f'  t={t:2d}s   {cols}   total: {sum(rates.values()):5.1f} Mbps', flush=True)


def main():
    setLogLevel('warning')
    net = start()
    try:
        buf = configure(net, RATE, RTT, 1.0, 'pfifo')
        r1, bott = bottleneck(net)
        for label, (src, dst, port, _) in FLOWS.items():
            bg(net.get(dst), f'iperf3 -s -p {port} -i 1 --forceflush > /tmp/demo_{src}.log 2>&1')

        stage(f'1. Dumbbell is up: {RATE} Mbps bottleneck on {bott}, {RTT} ms RTT, '
              f'pfifo buffer of {buf} packets (1x BDP). Show the tc config')
        print(r1.cmd(f'tc qdisc show dev {bott}'))
        active = []
        for step, label in [('2. Start one CUBIC flow', 'CUBIC h1'),
                            ('3. Add a BBR flow and watch the shares shift', 'BBR h2'),
                            ('4. Add UDP at 100% of the link and watch TCP collapse', 'UDP h4')]:
            stage(step)
            src, dst, port, opts = FLOWS[label]
            bg(net.get(src), f'iperf3 -c {IP[dst]} -p {port} -t 600 {opts} > /dev/null 2>&1')
            active.append(label)
            watch(active, 15)
        stage('5. Switch the bottleneck queue to fq_codel and watch TCP recover')
        apply_bottleneck(r1, bott, RATE, buf, 'fq_codel')
        print(r1.cmd(f'tc qdisc show dev {bott}'))
        watch(active, 20)
        stage('6. Done. Switch to Wireshark for the fast-retransmit capture (E5.3)')
    finally:
        for host in net.hosts:
            host.cmd('pkill -9 iperf3')
        net.stop()


if __name__ == '__main__':
    main()

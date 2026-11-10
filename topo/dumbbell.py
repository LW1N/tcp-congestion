"""Dumbbell: senders h1-h4 on s1, router r1, receivers h5-h8 on s2, probe pair hp -> hr.

The bottleneck is r1's egress toward s2 (r1-eth1). It must be a router, not a switch port:
since Linux 4.19 a packet keeps its sending socket's ownership across veth and Open vSwitch,
so a queue on a switch port pushes back on the sender (UDP blocks, TCP Small Queues caps the
queue at a few packets). IP forwarding in r1 drops that ownership, like a real router.

Run from the project root:  sudo python3 -u -m topo.dumbbell [--cli]
"""
import argparse

from mininet.cli import CLI
from mininet.link import Link
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Node, OVSBridge
from mininet.topo import Topo
from mininet.util import dumpNodeConnections

from topo.shaping import apply_bottleneck, apply_path, bdp_packets

PAIRS = 4                                   # h1->h5, h2->h6, h3->h7, h4->h8
SENDERS = [f'h{i}' for i in range(1, PAIRS + 1)]
RECEIVERS = [f'h{i + PAIRS}' for i in range(1, PAIRS + 1)]
SENDER_NET, RECEIVER_NET = '10.0.0', '10.0.1'
IP = {h: f'{SENDER_NET}.{h[1:]}' for h in SENDERS}
IP.update({h: f'{RECEIVER_NET}.{h[1:]}' for h in RECEIVERS})
IP.update(hp=f'{SENDER_NET}.9', hr=f'{RECEIVER_NET}.10',
          r1_left=f'{SENDER_NET}.254', r1_right=f'{RECEIVER_NET}.254')
BOTTLENECK_INTF = 'r1-eth1'

# Large socket buffers so the window is never limited by the host at 150 ms x 4 BDP.
HOST_SYSCTLS = [
    'net.ipv4.tcp_rmem="4096 131072 33554432"',
    'net.ipv4.tcp_wmem="4096 16384 33554432"',
    'net.ipv4.tcp_no_metrics_save=1',
    'net.ipv6.conf.all.disable_ipv6=1',     # keeps captures free of IPv6 chatter
    'net.ipv6.conf.default.disable_ipv6=1',
]


class Router(Node):
    """A Linux host with IP forwarding on."""
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -q -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -q -w net.ipv4.ip_forward=0')
        super().terminate()


class Dumbbell(Topo):
    def build(self):
        s1, s2 = self.addSwitch('s1'), self.addSwitch('s2')
        r1 = self.addNode('r1', cls=Router, ip=IP['r1_left'] + '/24')
        # Added first, so s1-eth1 / s2-eth1 face the router and r1-eth1 is the bottleneck.
        self.addLink(s1, r1, intfName2='r1-eth0', params2={'ip': IP['r1_left'] + '/24'})
        self.addLink(r1, s2, intfName1='r1-eth1', params1={'ip': IP['r1_right'] + '/24'})
        left, right = f'via {IP["r1_left"]}', f'via {IP["r1_right"]}'
        for snd, rcv in zip(SENDERS, RECEIVERS):
            self.addLink(self.addHost(snd, ip=IP[snd] + '/24', defaultRoute=left), s1)
            self.addLink(self.addHost(rcv, ip=IP[rcv] + '/24', defaultRoute=right), s2)
        self.addLink(self.addHost('hp', ip=IP['hp'] + '/24', defaultRoute=left), s1)
        self.addLink(self.addHost('hr', ip=IP['hr'] + '/24', defaultRoute=right), s2)


def static_arp(net):
    """Static ARP everywhere: otherwise a path's first packet waits for an ARP exchange across
    the delayed link (about 2x RTT), which skews pings and the idle-RTT check in run.py."""
    net.staticArp()
    r1 = net.get('r1')
    for host in net.hosts:
        if host is r1:
            continue
        gw = r1.intf('r1-eth0' if host.IP().startswith(SENDER_NET + '.') else 'r1-eth1')
        host.cmd(f'ip neigh replace {gw.IP()} lladdr {gw.MAC()} dev {host.defaultIntf()} nud permanent')
        r1.cmd(f'ip neigh replace {host.IP()} lladdr {host.MAC()} dev {gw} nud permanent')


def start():
    """Build and start the network with offloads off and host TCP settings applied."""
    net = Mininet(topo=Dumbbell(), switch=OVSBridge, controller=None,
                  link=Link, autoSetMacs=True)
    net.start()
    static_arp(net)
    for node in net.hosts + net.switches:
        for intf in node.intfList():
            if intf.name != 'lo':
                node.cmd(f'ethtool -K {intf.name} tso off gso off gro off')
    for host in net.hosts:
        for sysctl in HOST_SYSCTLS:
            host.cmd(f'sysctl -q -w {sysctl}')
    return net


def bottleneck(net):
    """(node, interface) of the bottleneck queue."""
    return net.get('r1'), BOTTLENECK_INTF


def bottleneck_intf(net):
    return BOTTLENECK_INTF


def receiver_port(net, host):
    """s2's interface facing a receiver; its netem delay sets that path's RTT."""
    return net.get('s2').connectionsTo(net.get(host))[0][0].name


def configure(net, rate=50, rtt=40, buf_bdp=1.0, qdisc='pfifo', path_rtts=None):
    """Shape the bottleneck and set every path's delay. Returns the buffer in packets.

    path_rtts maps a receiver name to its RTT; receivers not listed get `rtt`.
    The buffer is sized from the nominal `rtt`.
    """
    path_rtts = path_rtts or {}
    buf = bdp_packets(rate, rtt, buf_bdp)
    node, intf = bottleneck(net)
    apply_bottleneck(node, intf, rate, buf, qdisc)
    for rcv in RECEIVERS + ['hr']:
        apply_path(net.get('s2'), receiver_port(net, rcv), path_rtts.get(rcv, rtt))
    return buf


def main():
    parser = argparse.ArgumentParser(description='Start the dumbbell and print its configuration.')
    parser.add_argument('--rate', type=float, default=50)
    parser.add_argument('--rtt', type=float, default=40)
    parser.add_argument('--buf-bdp', type=float, default=1.0)
    parser.add_argument('--qdisc', default='pfifo', choices=['pfifo', 'red', 'fq_codel'])
    parser.add_argument('--cli', action='store_true', help='drop into the Mininet CLI')
    args = parser.parse_args()

    # 'output', not 'warning': the CLI prints host command output (h1 ping ...) at this level.
    setLogLevel('output')
    net = start()
    try:
        buf = configure(net, args.rate, args.rtt, args.buf_bdp, args.qdisc)
        r1, bott = bottleneck(net)
        print(f'== Topology (bottleneck {bott} on router r1, buffer {buf} packets)')
        dumpNodeConnections(net.hosts)
        for link in net.links:
            print(' ', link)
        print('\n== Addresses')
        for name in SENDERS + ['hp'] + RECEIVERS + ['hr']:
            print(f'  {name}: {net.get(name).IP()}')
        print(f'  r1: r1-eth0 {IP["r1_left"]}, r1-eth1 {IP["r1_right"]}')
        print(f'\n== Bottleneck qdisc and class on {bott}')
        print(r1.cmd(f'tc -s qdisc show dev {bott}'))
        print(r1.cmd(f'tc class show dev {bott}'))
        print('== Path delays on s2')
        for rcv in RECEIVERS + ['hr']:
            port = receiver_port(net, rcv)
            print(f'{rcv} via {port}:', net.get('s2').cmd(f'tc qdisc show dev {port}').strip())
        print('\n== Offloads on h1-eth0')
        print(net.get('h1').cmd("ethtool -k h1-eth0 | grep -E "
                                "'tcp-segmentation-offload|generic-(segmentation|receive)-offload'"))
        print('== h1 -> h5 ping')
        print(net.get('h1').cmd(f"ping -c 5 {IP['h5']} | tail -2"))
        if args.cli:
            CLI(net)
    finally:
        net.stop()


if __name__ == '__main__':
    main()

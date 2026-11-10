"""Link shaping with tc: the bottleneck queue on router r1 and per-path delay on s2."""
import math

MTU = 1500


def bdp_packets(rate_mbit, rtt_ms, k=1.0):
    """Buffer of k x BDP, in full-size packets (at least 2)."""
    bdp_bytes = rate_mbit * 1e6 / 8 * rtt_ms / 1e3
    return max(2, math.ceil(k * bdp_bytes / MTU))


def _tc(node, cmd):
    """Run a tc command on a node; raise if it fails, so a bad config never runs silently."""
    out = node.cmd(f'{cmd} 2>&1; echo "rc=$?"')
    if not out.strip().endswith('rc=0'):
        raise RuntimeError(f'tc failed on {node.name}: {cmd}\n{out}')


def qdisc_spec(qdisc, rate_mbit, buf_pkts):
    """Child qdisc under htb. The hard queue limit is buf_pkts for all three."""
    if qdisc == 'pfifo':
        return f'pfifo limit {buf_pkts}'
    if qdisc == 'fq_codel':
        return f'fq_codel limit {buf_pkts}'
    if qdisc == 'red':
        limit = buf_pkts * MTU                       # hard limit in bytes
        qmin = max(MTU, limit // 6)                  # start early marking at 1/6 full
        qmax = max(qmin + MTU, limit // 2)           # drop probability reaches max at 1/2 full
        burst = math.ceil((2 * qmin + qmax) / (3 * MTU)) + 1
        return (f'red limit {limit} min {qmin} max {qmax} avpkt {MTU} '
                f'burst {burst} bandwidth {rate_mbit}mbit probability 0.1')
    raise ValueError(f'unknown qdisc {qdisc}')


def apply_bottleneck(node, intf, rate_mbit, buf_pkts, qdisc='pfifo'):
    """htb sets the rate; its child qdisc is the only queue, so buffer size is exact."""
    node.cmd(f'tc qdisc del dev {intf} root 2>/dev/null')
    _tc(node, f'tc qdisc add dev {intf} root handle 1: htb default 10')
    _tc(node, f'tc class add dev {intf} parent 1: classid 1:10 htb '
              f'rate {rate_mbit}mbit ceil {rate_mbit}mbit quantum {MTU + 14}')
    _tc(node, f'tc qdisc add dev {intf} parent 1:10 handle 20: '
              f'{qdisc_spec(qdisc, rate_mbit, buf_pkts)}')


def apply_path(node, intf, delay_ms):
    """Propagation delay on the data path. The large limit means netem itself never drops."""
    _tc(node, f'tc qdisc replace dev {intf} root netem delay {delay_ms}ms limit 100000')

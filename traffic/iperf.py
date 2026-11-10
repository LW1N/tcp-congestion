"""iperf3 servers and clients inside Mininet hosts."""
import json


def bg(host, cmd):
    """Start a shell command in the background on a host and return its PID."""
    out = host.cmd(f'{cmd} & echo "pid=$!"')
    for line in reversed(out.splitlines()):
        if line.startswith('pid='):
            return int(line[4:])
    raise RuntimeError(f'could not start on {host.name}: {cmd}\n{out}')


def alive(host, pid):
    return host.cmd(f'kill -0 {pid} 2>/dev/null; echo $?').strip().endswith('0')


def start_server(host, port, outfile):
    """One-off server (-1): it exits after its single test."""
    return bg(host, f'iperf3 -s -p {port} -1 -J > {outfile} 2>&1')


def start_client(host, dst_ip, port, duration, outfile, cca=None, omit=0,
                 udp_mbit=None, udp_len=1200, delay=0):
    """TCP flow with an explicit CCA, or a UDP flow at a fixed rate when udp_mbit is set.

    `delay` seconds pass before the client starts (staggered and late-UDP runs).
    """
    cmd = f'iperf3 -c {dst_ip} -p {port} -t {duration} -i 1 -J'
    if udp_mbit:
        cmd += f' -u -b {udp_mbit}M -l {udp_len}'
    else:
        cmd += f' -C {cca} -O {omit}'
    return bg(host, f'(sleep {delay}; {cmd}) > {outfile} 2>&1')


def client_ok(outfile):
    """True when the client wrote a complete JSON result without an error."""
    try:
        with open(outfile) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    return 'end' in data and 'error' not in data

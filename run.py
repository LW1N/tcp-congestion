"""Run an experiment file: every configuration x every trial, unattended.

  sudo python3 -u run.py experiments/s1_competing.yaml [--dry-run] [--only ID] [--trials N]
                         [--staggered] [--udp-delay S] [--capture] [--resume DIR]
"""
import argparse
import itertools
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

ID_KEYS = ['n', 'udp_pct', 'buf_bdp', 'rtt', 'rtt_mode', 'cca', 'cca_mix', 'qdisc']
ID_PREFIX = {'n': 'n', 'udp_pct': 'udp', 'buf_bdp': 'b', 'rtt': 'rtt'}
MIXED_RTTS = {2: [20, 80], 4: [20, 40, 60, 80]}
BASE_PORT = 5200
SETUP_SECONDS = 12            # build, warm-up, teardown per trial (for the time estimate)


# ---------- configurations ----------

def expand(entry):
    """{'n': [2, 4], 'qdisc': 'pfifo'} -> [{'n': 2, 'qdisc': 'pfifo'}, {'n': 4, ...}]"""
    keys = list(entry)
    values = [v if isinstance(v, list) else [v] for v in entry.values()]
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def config_id(params):
    parts = []
    for key in ID_KEYS:
        if key in params:
            value = params[key]
            value = f'{value:g}' if isinstance(value, float) else value
            parts.append(f'{ID_PREFIX.get(key, "")}{value}')
    return '-'.join(parts)


def load_configs(spec):
    """Every configuration in the grid, with its ID, merged parameters and capture flag."""
    captures = [c for entry in spec.get('capture', []) for c in expand(entry)]
    configs = []
    for entry in spec['grid']:
        for params in expand(entry):
            cfg = {**spec.get('defaults', {}), **params}
            cfg['id'] = config_id(params)
            cfg['capture'] = any(all(cfg.get(k) == v for k, v in c.items()) for c in captures)
            configs.append(cfg)
    ids = [c['id'] for c in configs]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f'duplicate configuration IDs: {sorted(dupes)}')
    return configs


def flow_plan(cfg, duration, staggered=False, udp_delay=0):
    """The flows of one configuration: who sends to whom, with which CCA, RTT and start time."""
    n = cfg.get('n', 1)
    if cfg.get('cca_mix') == 'cubic+bbr':
        ccas = ['cubic' if i % 2 == 0 else 'bbr' for i in range(n)]
    else:
        ccas = [cfg.get('cca_mix') or cfg.get('cca', 'cubic')] * n
    rtts = MIXED_RTTS[n] if cfg.get('rtt_mode') == 'mixed' else [cfg['rtt']] * n
    flows = []
    for i in range(n):
        start = 10 * i if staggered else 0
        flows.append(dict(kind='tcp', src=f'h{i + 1}', dst=f'h{i + 5}', port=BASE_PORT + i + 1,
                          cca=ccas[i], rtt=rtts[i], start=start, duration=duration - start))
    if 'udp_pct' in cfg:
        flows.append(dict(kind='udp', src='h4', dst='h8', port=BASE_PORT + 4,
                          udp_mbit=cfg['rate'] * cfg['udp_pct'] / 100, udp_len=cfg.get('udp_len', 1200),
                          rtt=cfg['rtt'], start=udp_delay, duration=duration - udp_delay))
    return flows


# ---------- one trial ----------

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def cleanup():
    # The [x] trick stops pkill -f from matching (and killing) the shell running it.
    sh('pkill -9 -f "[i]perf3 -[sc]"; pkill -9 tcpdump; pkill -9 -f "[p]ing -D"')
    sh('mn -c > /dev/null 2>&1')


def idle_rtt_ok(net, rtt):
    """Minimum probe RTT before traffic must be within 10% (at least 2 ms) of its target.

    The minimum, not the average: the VM adds a few ms of wake-up jitter to some pings,
    which says nothing about whether the configured delay is right.
    """
    from topo.dumbbell import IP
    out = net.get('hp').cmd(f"ping -c 5 -i 0.2 {IP['hr']} | tail -1")
    try:
        rtt_min = float(out.split('=')[1].split('/')[0])
    except (IndexError, ValueError):
        return False, out
    return abs(rtt_min - rtt) <= max(0.1 * rtt, 2.0), rtt_min


def run_trial(cfg, flows, trial_dir, spec, capture):
    from mininet.log import setLogLevel
    from topo.dumbbell import IP, bottleneck, configure, start
    from traffic import iperf, probes

    setLogLevel('warning')
    trial_dir.mkdir(parents=True, exist_ok=True)
    meta = dict(config=cfg, flows=flows, capture=capture, kernel=sh('uname -r'),
                commit=sh('git rev-parse --short HEAD 2>/dev/null') or 'none',
                omit=spec.get('omit', 0))
    net = start()
    running = []
    try:
        path_rtts = {f['dst']: f['rtt'] for f in flows}
        meta['buffer_pkts'] = configure(net, cfg['rate'], cfg['rtt'], cfg.get('buf_bdp', 1.0),
                                        cfg.get('qdisc', 'pfifo'), path_rtts)
        ok, idle = idle_rtt_ok(net, cfg['rtt'])
        meta['idle_rtt_ms'] = idle
        if not ok:
            raise RuntimeError(f'idle RTT {idle} ms is more than 10% off {cfg["rtt"]} ms')

        r1, bott = bottleneck(net)
        for f in flows:
            iperf.start_server(net.get(f['dst']), f['port'], trial_dir / f'srv_{f["port"]}.json')
        running += [probes.ping(net.get('hp'), IP['hr'], trial_dir / 'ping.txt'),
                    probes.qdisc_sampler(r1, bott, trial_dir / 'qdisc.txt')]
        for f in flows:
            if f['kind'] == 'tcp':
                running.append(probes.ss_sampler(net.get(f['src']), IP[f['dst']],
                                                 trial_dir / f'ss_{f["src"]}.txt'))
        if capture:
            running += [probes.tcpdump(r1, bott, trial_dir / 'bottleneck.pcap'),
                        probes.tcpdump(net.get('h1'), 'h1-eth0', trial_dir / 'sender_h1.pcap')]
        time.sleep(2)                                   # servers up, idle RTT samples recorded

        meta['traffic_start'] = time.time()
        clients = []
        for f in flows:
            out = trial_dir / f'{f["src"]}_{f["kind"]}.json'
            f['out'] = out.name
            host = net.get(f['src'])
            pid = iperf.start_client(host, IP[f['dst']], f['port'], f['duration'], out,
                                     cca=f.get('cca'), omit=spec.get('omit', 0),
                                     udp_mbit=f.get('udp_mbit'), udp_len=f.get('udp_len', 1200),
                                     delay=f['start'])
            clients.append((host, pid))
        deadline = time.time() + max(f['start'] + f['duration'] for f in flows) + 20
        while any(iperf.alive(h, p) for h, p in clients) and time.time() < deadline:
            time.sleep(1)
        meta['traffic_end'] = time.time()
        time.sleep(1)                                   # a little loaded-to-idle tail
    finally:
        probes.stop(running)
        net.stop()
        cleanup()

    bad = [f['out'] for f in flows if not iperf.client_ok(trial_dir / f['out'])]
    if bad:
        raise RuntimeError(f'iperf3 failed: {bad}')
    (trial_dir / 'meta.json').write_text(json.dumps(meta, indent=2, default=str))
    (trial_dir / 'done').touch()


# ---------- main ----------

def fix_ownership(path):
    """Results are written as root; hand them back to the user who ran sudo."""
    uid, gid = os.environ.get('SUDO_UID'), os.environ.get('SUDO_GID')
    if uid and gid:
        sh(f'chown -R {uid}:{gid} {path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('spec')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--only', action='append', help='run only this config ID (repeatable)')
    parser.add_argument('--trials', type=int, help='override the trial count')
    parser.add_argument('--staggered', action='store_true', help='start TCP flows 10 s apart')
    parser.add_argument('--udp-delay', type=float, default=0, help='start UDP this many s late')
    parser.add_argument('--capture', action='store_true', help='capture packets in every trial')
    parser.add_argument('--resume', help='continue an interrupted run in this results folder')
    parser.add_argument('--seed', type=int, default=206)
    args = parser.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text())
    configs = load_configs(spec)
    if args.only:
        unknown = set(args.only) - {c['id'] for c in configs}
        if unknown:
            sys.exit(f'unknown IDs {sorted(unknown)}; valid: {[c["id"] for c in configs]}')
        configs = [c for c in configs if c['id'] in args.only]
    trials = args.trials or spec['trials']
    duration = spec['duration']
    per_trial = duration + SETUP_SECONDS

    print(f'{spec["scenario"]}: {len(configs)} configurations x {trials} trials = '
          f'{len(configs) * trials} runs, about {len(configs) * trials * per_trial / 3600:.1f} h')
    print(f'captured configurations: {[c["id"] for c in configs if c["capture"]]}')
    if args.dry_run:
        for c in configs:
            print(f'  {c["id"]}')
        return
    if os.geteuid() != 0:
        sys.exit('run with sudo')

    tag = datetime.now().strftime('%Y%m%d-%H%M%S')
    if args.staggered:
        tag += '-staggered'
    if args.udp_delay:
        tag += f'-udpdelay{args.udp_delay:g}'
    out_root = (Path(args.resume) if args.resume else Path('results') / spec['scenario'] / tag).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    print(f'writing to {out_root}')

    rng = random.Random(args.seed)
    cleanup()
    failures = []
    try:
        for trial in range(1, trials + 1):              # trials interleaved, configs shuffled
            order = configs[:]
            rng.shuffle(order)
            for cfg in order:
                trial_dir = out_root / cfg['id'] / f'trial_{trial}'
                if (trial_dir / 'done').exists():
                    continue
                flows = flow_plan(cfg, duration, args.staggered, args.udp_delay)
                capture = args.capture or (cfg['capture'] and trial == 1)
                for attempt in (1, 2, 3):
                    print(f'{datetime.now():%H:%M:%S} {cfg["id"]} trial {trial} '
                          f'attempt {attempt}{" [capture]" if capture else ""}', flush=True)
                    try:
                        run_trial(cfg, flows, trial_dir, spec, capture)
                        break
                    except Exception as exc:                # noqa: BLE001 - retry any failure
                        print(f'  failed: {exc}', flush=True)
                        cleanup()
                        time.sleep(2)
                else:
                    failures.append(f'{cfg["id"]} trial {trial}')
    finally:
        fix_ownership(out_root)
    print(f'finished: {out_root}' + (f'\nFAILED (rerun with --resume): {failures}' if failures else ''))


if __name__ == '__main__':
    main()

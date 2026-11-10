"""Generate fake trial folders shaped like run.py output, to test the analysis pipeline."""
import json
import random
import sys
from pathlib import Path

import yaml

sys.path.insert(0, '.')
from run import flow_plan, load_configs  # noqa: E402

rng = random.Random(1)


def tcp_json(gbps, cca, duration, omit, rtt):
    intervals = []
    for i in range(omit + duration):
        bps = gbps * 1e6 * rng.uniform(0.9, 1.1)
        stream = dict(socket=5, start=0, end=1, seconds=1.0, bytes=bps / 8, bits_per_second=bps,
                      retransmits=rng.randint(0, 3), snd_cwnd=int(rng.uniform(150, 330) * 1448),
                      rtt=int((rtt + rng.uniform(0, 40)) * 1000), omitted=i < omit, sender=True)
        intervals.append(dict(streams=[stream], sum=dict(start=0, end=1, seconds=1.0, bytes=bps / 8,
                                                         bits_per_second=bps, retransmits=stream['retransmits'],
                                                         omitted=i < omit, sender=True)))
    total = gbps * 1e6 * duration / 8
    end = dict(streams=[dict(sender=dict(bytes=total, bits_per_second=gbps * 1e6, retransmits=40,
                                         mean_rtt=int((rtt + 20) * 1000), max_rtt=int((rtt + 45) * 1000)),
                             receiver=dict(bytes=total, bits_per_second=gbps * 1e6 * 0.99))],
               sum_sent=dict(bytes=total, bits_per_second=gbps * 1e6, retransmits=40),
               sum_received=dict(bytes=total, bits_per_second=gbps * 1e6 * 0.99),
               sender_tcp_congestion=cca, receiver_tcp_congestion=cca)
    return dict(start={}, intervals=intervals, end=end)


def udp_json(mbit, duration, loss):
    intervals = [dict(streams=[dict(bits_per_second=mbit * 1e6, packets=5000, omitted=False)],
                      sum=dict(start=0, end=1, seconds=1.0, bytes=mbit * 1e6 / 8, bits_per_second=mbit * 1e6,
                               packets=5000, omitted=False)) for _ in range(duration)]
    end = dict(sum=dict(bytes=mbit * 1e6 * duration / 8, bits_per_second=mbit * 1e6, jitter_ms=rng.uniform(0.1, 3),
                        lost_packets=100, packets=300000, lost_percent=loss))
    return dict(start={}, intervals=intervals, end=end)


def make(spec_path, trials=3, special=None):
    spec = yaml.safe_load(Path(spec_path).read_text())
    tag = '20261101-000000' + (f'-{special}' if special else '')
    configs = load_configs(spec)
    if special == 'staggered':
        configs = [c for c in configs if c['id'] == 'n2-equal-cubic+bbr-pfifo']
    if special == 'udpdelay20':
        configs = [c for c in configs if c['id'].startswith('udp100-cubic')]
    for cfg in configs:
        for trial in range(1, trials + 1):
            d = Path('results') / spec['scenario'] / tag / cfg['id'] / f'trial_{trial}'
            d.mkdir(parents=True, exist_ok=True)
            flows = flow_plan(cfg, spec['duration'], special == 'staggered', 20 if special == 'udpdelay20' else 0)
            t0 = 1_800_000_000.0
            udp_mbit = sum(f.get('udp_mbit', 0) for f in flows)
            tcp_share = max(1.0, cfg['rate'] - udp_mbit * (0.5 if cfg.get('qdisc') == 'fq_codel' else 0.95))
            n_tcp = sum(f['kind'] == 'tcp' for f in flows)
            for f in flows:
                f['out'] = f'{f["src"]}_{f["kind"]}.json'
                if f['kind'] == 'tcp':
                    bias = 1.3 if f['cca'] == 'bbr' else 0.8 if cfg.get('cca_mix') == 'cubic+bbr' else 1.0
                    bias *= 40 / f['rtt'] if cfg.get('rtt_mode') == 'mixed' else 1
                    data = tcp_json(tcp_share / n_tcp * bias * rng.uniform(0.95, 1.05), f['cca'],
                                    f['duration'], spec['omit'], f['rtt'])
                else:
                    data = udp_json(f['udp_mbit'], f['duration'], rng.uniform(0, 30))
                (d / f['out']).write_text(json.dumps(data))
            buf = int(cfg.get('buf_bdp', 1) * 167)
            qd = 0 if cfg.get('qdisc') == 'fq_codel' else cfg.get('buf_bdp', 1) * cfg['rtt']
            ping = [f'[{t0 + t * 0.2:.6f}] 64 bytes from 10.0.0.10: icmp_seq={i} ttl=64 '
                    f'time={cfg["rtt"] + (rng.uniform(0, qd) if t >= 0 else 0) + rng.uniform(0, 1):.2f} ms'
                    for i, t in enumerate(range(-10, 310))]
            (d / 'ping.txt').write_text('\n'.join(ping))
            q, wire_bytes = [], cfg['rate'] * 1e6 / 8 * 0.5 * rng.uniform(0.9, 1.0)   # per sample
            for i, t in enumerate(range(-4, 130)):
                q += [f'T {t0 + t * 0.5:.6f}', 'qdisc htb 1: root refcnt 2 r2q 10 default 0x10',
                      ' Sent 1 bytes 1 pkt (dropped 0, overlimits 0 requeues 0)', ' backlog 0b 0p requeues 0',
                      f'qdisc pfifo 20: parent 1:10 limit {buf}p',
                      f' Sent {int(max(t, 0) * wire_bytes)} bytes {i} pkt (dropped {i * 3}, overlimits 0 requeues 0)',
                      f' backlog 58Kb {rng.randint(0, buf)}p requeues 0']
            (d / 'qdisc.txt').write_text('\n'.join(q))
            ss = []
            for i in range(600):
                ss += [f'T {t0 + i * 0.1:.6f}', 'State Recv-Q Send-Q Local Address:Port Peer Address:Port',
                       'ESTAB 0 0 10.0.0.1:40000 10.0.0.5:5201',
                       '\t cubic wscale:9,9 rto:204 rtt:40.5/0.2 mss:1448 cwnd:10 bytes_acked:200 segs_out:5',
                       'ESTAB 0 1000 10.0.0.1:40002 10.0.0.5:5201',
                       f'\t cubic wscale:9,9 rto:244 rtt:{40 + (i % 70) * 0.5:.1f}/1.1 mss:1448 '
                       f'cwnd:{167 + (i % 70) * 2} ssthresh:150 bytes_acked:{1000000 * i} segs_out:9']
            (d / 'ss_h1.txt').write_text('\n'.join(ss))
            meta = dict(config=cfg, flows=flows, capture=False, omit=spec['omit'], buffer_pkts=buf,
                        idle_rtt_ms=cfg['rtt'], traffic_start=t0, traffic_end=t0 + spec['duration'] + 1)
            (d / 'meta.json').write_text(json.dumps(meta))
            (d / 'done').touch()


for s in ['experiments/s1_competing.yaml', 'experiments/s2_tcp_udp.yaml', 'experiments/s3_buffer_delay.yaml']:
    make(s)
make('experiments/s1_competing.yaml', 1, 'staggered')
make('experiments/s2_tcp_udp.yaml', 1, 'udpdelay20')
print('fake data written')

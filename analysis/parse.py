"""Turn raw trial folders into tidy CSVs in data/.

  python3 -m analysis.parse s1      (or s2, s3, or all)

Writes data/<scenario>_{flows,trials,series,ss,ping}.csv. Raw files are never modified.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS, DATA = Path('results'), Path('data')
MSS = 1448
PARAMS = ['n', 'cca', 'cca_mix', 'rtt_mode', 'qdisc', 'buf_bdp', 'rtt', 'udp_pct', 'rate']
PING_RE = re.compile(r'^\[(\d+\.\d+)\].*time=([\d.]+) ms')
SS_CWND_RE = re.compile(r'\bcwnd:(\d+)')
SS_RTT_RE = re.compile(r'\brtt:([\d.]+)/')
SS_ACKED_RE = re.compile(r'\bbytes_acked:(\d+)')


def trial_dirs(scenario):
    """Completed trials. A (config, trial) run more than once keeps its newest copy;
    staggered and late-UDP runs are kept separately as 'special'."""
    chosen = {}
    for done in sorted((RESULTS / scenario).glob('*/*/trial_*/done')):
        d = done.parent
        run = d.parent.parent.name
        special = 'staggered' in run or 'udpdelay' in run
        key = (run if special else '', d.parent.name, d.name)
        chosen[key] = (d, run, special)                 # sorted order -> newest wins
    return chosen.values()


def parse_ping(path, t0):
    rows = []
    for line in path.read_text(errors='replace').splitlines():
        m = PING_RE.match(line)
        if m:
            rows.append((float(m.group(1)) - t0, float(m.group(2))))
    return rows


def parse_qdisc(path, t0):
    """(t, backlog_pkts, cumulative_drops, cumulative_sent_bytes) of the child qdisc (parent 1:10)
    at each sample. Sent bytes count whole frames, headers included, as the shaper does."""
    rows, t, child, drops, sent = [], None, False, None, None
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('T '):
            t, child = float(line[2:]) - t0, False
        elif line.startswith('qdisc'):
            child = 'parent 1:10' in line
        elif child and 'Sent' in line:
            m = re.search(r'dropped (\d+)', line)
            drops = int(m.group(1)) if m else None
            m = re.search(r'Sent (\d+) bytes', line)
            sent = int(m.group(1)) if m else None
        elif child and line.strip().startswith('backlog') and t is not None:
            m = re.search(r'(\d+)p', line)
            if m:
                rows.append((t, int(m.group(1)), drops, sent))
    return rows


def parse_ss(path, t0):
    """(t, cwnd_pkts, rtt_ms) of the data connection (the socket with the most bytes acked)."""
    rows, t, best = [], None, None
    def flush():
        if t is not None and best is not None:
            rows.append((t, best[1], best[2]))
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('T '):
            flush()
            t, best = float(line[2:]) - t0, None
        elif 'cwnd:' in line:
            acked = SS_ACKED_RE.search(line)
            cwnd, rtt = SS_CWND_RE.search(line), SS_RTT_RE.search(line)
            if acked and cwnd and rtt and (best is None or int(acked.group(1)) > best[0]):
                best = (int(acked.group(1)), int(cwnd.group(1)), float(rtt.group(1)))
    flush()
    return rows


def measured(flow, omit):
    """(start, end) in traffic time of the part iperf3 measures: TCP leaves out its omit period."""
    lag = omit if flow['kind'] == 'tcp' else 0
    return flow['start'] + lag, flow['start'] + flow['duration'] + lag


def in_window(data, start, window):
    """Interval sums of an iperf3 JSON that lie inside the window (traffic time)."""
    lo, hi = window
    out, t = [], start
    for interval in data.get('intervals', []):
        s = interval['sum']
        t += s['seconds']
        if t - s['seconds'] >= lo - 0.05 and t <= hi + 0.1:
            out.append(s)
    return out


def parse_flow(path, flow, window, omit):
    """Summary row and per-second series of one iperf3 client.

    Metrics cover the window in which every flow of the trial is measured. When a flow is measured
    for longer (UDP stops at 60 s while TCP runs 65 s with -O 5; staggered starts), its summary is
    recomputed from the per-second intervals inside the window, receiver side from the server JSON."""
    data = json.loads(path.read_text())
    end = data['end']
    lo, hi = measured(flow, omit)
    partial = lo < window[0] - 0.5 or hi > window[1] + 0.5
    server = path.parent / f"srv_{flow['port']}.json"
    recv_iv = in_window(json.loads(server.read_text()), flow['start'], window) if partial else []
    row = dict(src=flow['src'], kind=flow['kind'], flow_cca=flow.get('cca'),
               path_rtt=flow['rtt'], start=flow['start'])
    if flow['kind'] == 'tcp':
        sent, recv = end['sum_sent'], end['sum_received']
        stream = end['streams'][0]['sender']
        goodput, retransmits, sent_bytes = (recv['bits_per_second'] / 1e6,
                                            sent.get('retransmits', 0), sent['bytes'])
        if partial:
            sent_iv = in_window(data, flow['start'], window)
            goodput = 8 * sum(s['bytes'] for s in recv_iv) / max(sum(s['seconds'] for s in recv_iv), 1e-9) / 1e6
            retransmits = sum(s.get('retransmits', 0) for s in sent_iv)
            sent_bytes = sum(s['bytes'] for s in sent_iv)
        row.update(goodput_mbps=goodput, retransmits=retransmits, bytes_sent=sent_bytes,
                   retrans_pct=100 * retransmits * MSS / max(sent_bytes, 1),
                   mean_rtt_ms=stream.get('mean_rtt', np.nan) / 1e3,
                   max_rtt_ms=stream.get('max_rtt', np.nan) / 1e3,
                   cca_reported=end.get('sender_tcp_congestion'))
    else:
        summary = next(end[k] for k in ('sum_received', 'sum', 'sum_sent')
                       if k in end and 'lost_percent' in end[k])
        sent_bps = end.get('sum_sent', end.get('sum', summary))['bits_per_second']
        goodput = sent_bps * (1 - summary['lost_percent'] / 100) / 1e6
        jitter, loss = summary['jitter_ms'], summary['lost_percent']
        if partial and recv_iv:
            goodput = 8 * sum(s['bytes'] for s in recv_iv) / sum(s['seconds'] for s in recv_iv) / 1e6
            jitter = float(np.mean([s['jitter_ms'] for s in recv_iv]))
            loss = 100 * sum(s['lost_packets'] for s in recv_iv) / max(sum(s['packets'] for s in recv_iv), 1)
        row.update(goodput_mbps=goodput, udp_jitter_ms=jitter, udp_loss_pct=loss)
    series, t = [], flow['start']
    for interval in data.get('intervals', []):
        s = interval['sum']
        t += s['seconds']
        st = interval['streams'][0]
        series.append(dict(src=flow['src'], kind=flow['kind'], start=flow['start'], t=t,
                           omitted=s.get('omitted', False), mbps=s['bits_per_second'] / 1e6,
                           cwnd_kb=st.get('snd_cwnd', np.nan) / 1e3,
                           rtt_ms=st.get('rtt', np.nan) / 1e3, retrans=s.get('retransmits', 0)))
    return row, series


def parse_scenario(scenario):
    flows, trials, series, ss, pings = [], [], [], [], []
    for d, run, special in trial_dirs(scenario):
        meta = json.loads((d / 'meta.json').read_text())
        cfg, t0 = meta['config'], meta['traffic_start']
        base = {k: cfg.get(k) for k in PARAMS}
        base.update(config=cfg['id'], trial=int(d.name.split('_')[1]), run=run, special=special)
        # loaded window: the time every flow is measured, i.e. after the omit period until the
        # first flow ends. TCP clients run duration + omit (iperf3 -O) but UDP only duration, so in
        # S2 the window ends when UDP stops; traffic_end also counts teardown, which would dilute wire_mbps.
        omit = meta.get('omit', 0)
        spans = [measured(f, omit) for f in meta['flows']]
        window = (max(s for s, _ in spans), min(e for _, e in spans))
        for flow in meta['flows']:
            row, rows = parse_flow(d / flow['out'], flow, window, omit)
            flows.append({**base, **row})
            series += [{**base, **r} for r in rows]
        if cfg.get('n', 1) == 1 and (d / 'ss_h1.txt').exists():
            ss += [{**base, 't': t, 'cwnd_pkts': c, 'rtt_ms': r} for t, c, r in parse_ss(d / 'ss_h1.txt', t0)]

        lo, hi = window[0], min(meta['traffic_end'] - t0, window[1])
        ping = parse_ping(d / 'ping.txt', t0)
        idle = [r for t, r in ping if t < 0]
        loaded = [r for t, r in ping if lo <= t <= hi]
        pings += [{**base, 't': t, 'rtt_ms': r} for t, r in ping]
        q = [s for s in parse_qdisc(d / 'qdisc.txt', t0) if lo <= s[0] <= hi]
        drops = [dr for _, _, dr, _ in q if dr is not None]
        sent = [(t, sb) for t, _, _, sb in q if sb is not None]
        # bits the bottleneck put on the wire per second, headers included
        wire = (8 * (sent[-1][1] - sent[0][1]) / (sent[-1][0] - sent[0][0]) / 1e6
                if len(sent) > 1 and sent[-1][0] > sent[0][0] else np.nan)
        trials.append({**base,
                       'buffer_pkts': meta.get('buffer_pkts'),
                       'idle_rtt_ms': np.median(idle) if idle else meta.get('idle_rtt_ms'),
                       'probe_rtt_p50': np.median(loaded) if loaded else np.nan,
                       'probe_rtt_p95': np.percentile(loaded, 95) if loaded else np.nan,
                       'max_backlog_pkts': max((b for _, b, _, _ in q), default=np.nan),
                       'mean_backlog_pkts': np.mean([b for _, b, _, _ in q]) if q else np.nan,
                       'wire_mbps': wire,
                       'drops': drops[-1] - drops[0] if len(drops) > 1 else np.nan})
    if not trials:
        print(f'{scenario}: no completed trials under {RESULTS / scenario}')
        return
    DATA.mkdir(exist_ok=True)
    trials_df = pd.DataFrame(trials)
    trials_df['queue_delay_ms'] = trials_df['probe_rtt_p50'] - trials_df['idle_rtt_ms']
    for name, rows in [('flows', flows), ('series', series), ('ss', ss), ('ping', pings)]:
        pd.DataFrame(rows).to_csv(DATA / f'{scenario}_{name}.csv', index=False)
    trials_df.to_csv(DATA / f'{scenario}_trials.csv', index=False)
    print(f'{scenario}: {len(trials)} trials, {len(flows)} flows -> {DATA}/{scenario}_*.csv')


def main():
    scenarios = ['s1', 's2', 's3'] if sys.argv[1:] in ([], ['all']) else sys.argv[1:]
    for scenario in scenarios:
        parse_scenario(scenario)


if __name__ == '__main__':
    main()

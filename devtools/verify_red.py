"""Independent check of the RED follow-up findings from raw trial files only (no analysis/ code).

Recomputes per-trial goodput, Jain, srtt, backlog, early/tail drops and probe delay for s1r, s2r,
s3r and s3qr, reports provenance problems, and writes the rows as JSON for comparison with figures/.

  python3 devtools/verify_red.py rows.json
"""
import json, re, glob, statistics as st, sys, collections, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
RTT_RE = re.compile(r'\brtt:([\d.]+)/')
ACK_RE = re.compile(r'bytes_acked:(\d+)')


def jain(x):
    return sum(x) ** 2 / (len(x) * sum(v * v for v in x)) if sum(x) else float('nan')


def ss_srtt(path, lo, hi):
    """Mean srtt (ms) of the data socket (most bytes acked) over samples in [lo, hi] epoch seconds."""
    vals, t, best = [], None, None
    for line in open(path, errors='replace'):
        if line.startswith('T '):
            if t is not None and best and lo <= t <= hi:
                vals.append(best[1])
            t, best = float(line[2:]), None
        elif 'cwnd:' in line:
            a, r = ACK_RE.search(line), RTT_RE.search(line)
            if a and r and (best is None or int(a.group(1)) > best[0]):
                best = (int(a.group(1)), float(r.group(1)))
    return st.mean(vals) if vals else float('nan')


def qdisc_samples(path, lo, hi):
    """(backlog_pkts, child Sent bytes, early, pdrop) per sample of the child qdisc (handle 20:)."""
    out, t, child = [], None, False
    sent = None
    for line in open(path):
        if line.startswith('T '):
            t, child = float(line[2:]), False
        elif line.startswith('qdisc'):
            child = ' 20:' in line
        elif child and line.strip().startswith('Sent'):
            sent = int(line.split()[1])
        elif child and line.strip().startswith('backlog') and lo <= t <= hi:
            out.append([int(re.search(r'(\d+)p', line).group(1)), sent, t])
        elif child and 'early' in line and out and out[-1][2] == t:
            m = re.search(r'early (\d+) pdrop (\d+)', line)
            out[-1] += [int(m.group(1)), int(m.group(2))]
    return out


def ping_p50(path, lo, hi):
    v = []
    for line in open(path):
        m = re.match(r'\[([\d.]+)\].*time=([\d.]+)', line)
        if m and lo <= float(m.group(1)) <= hi:
            v.append(float(m.group(2)))
    return st.median(v) if v else float('nan')


rows = collections.defaultdict(list)
problems = []
for scen in ('s1r', 's2r', 's3r', 's3qr'):
    for meta_p in sorted(glob.glob(f'{ROOT}/{scen}/*/*/trial_*/meta.json')):
        d = os.path.dirname(meta_p)
        m = json.load(open(meta_p))
        c = m['config']
        if m.get('commit') != '139ea6a' or not m['kernel'].startswith('6.18.58.1'):
            problems.append(f'{d}: commit {m.get("commit")} kernel {m["kernel"]}')
        if not os.path.exists(f'{d}/done'):
            problems.append(f'{d}: no done marker')
        t0 = m['traffic_start']
        omit = m['omit']
        tcp = [f for f in m['flows'] if f['kind'] == 'tcp']
        # S2: TCP measured while UDP runs (5-60 s), others: omit .. omit+duration
        udp = [f for f in m['flows'] if f['kind'] == 'udp']
        lo = t0 + omit
        hi = t0 + (udp[0]['start'] + udp[0]['duration'] if udp else omit + tcp[0]['duration'])
        gp, srtt = [], []
        for f in tcp:
            j = json.load(open(f'{d}/{f["out"]}'))
            if j.get('error'):
                problems.append(f'{d}: {f["out"]} error {j["error"]}')
            iv = [i['sum'] for i in j['intervals']]
            # client intervals after the omit period are what iperf3 reports; keep those inside [lo, hi]
            t, b, s = t0 + f['start'], 0, 0
            for x in iv:
                t += x['seconds']
                if x.get('omitted'):
                    continue
                if t - x['seconds'] >= lo - 0.05 and t <= hi + 0.1:
                    b += x['bytes']; s += x['seconds']
            gp.append(8 * b / s / 1e6 if s else 0.0)
            srtt.append(ss_srtt(f'{d}/ss_{f["src"]}.txt', lo, hi))
        q = qdisc_samples(f'{d}/qdisc.txt', lo, hi)
        wire = 8 * (q[-1][1] - q[0][1]) / (q[-1][2] - q[0][2]) / 1e6
        bl = [x[0] for x in q]
        last = q[-1]
        rows[(scen, c['id'])].append(dict(
            trial=d.rsplit('_', 1)[1], gp=gp, rtts=[f['rtt'] for f in tcp], ccas=[f['cca'] for f in tcp],
            srtt=srtt, wire=wire, util=100 * wire / c['rate'], tcp_mbps=sum(gp), jain=jain(gp),
            mean_bl=st.mean(bl), max_bl=max(bl), frac_above_min=sum(b > 10.4 for b in bl) / len(bl),
            pdrop=last[4] if len(last) > 4 else None, early=last[3] if len(last) > 3 else None,
            probe=ping_p50(f'{d}/ping.txt', lo, hi) - m['idle_rtt_ms'], buf=m['buffer_pkts'],
            start=m['traffic_start'], gp_wire=sum(gp) / wire if wire else float('nan')))

print('PROBLEMS:', problems or 'none')
json.dump({f'{k[0]}|{k[1]}': v for k, v in rows.items()}, open(sys.argv[1], 'w'))
print('wrote', len(rows), 'configs')

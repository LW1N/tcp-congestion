"""Derived metrics, confidence intervals, and data-quality checks.

  python3 -m analysis.metrics s1            # write figures/s1_summary.csv
  python3 -m analysis.metrics s1 --check    # flag configurations that need more trials
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA, FIGURES = Path('data'), Path('figures')
PARAMS = ['n', 'cca', 'cca_mix', 'rtt_mode', 'qdisc', 'buf_bdp', 'rtt', 'udp_pct', 'rate']
SUMMARY_METRICS = ['utilization_pct', 'tcp_mbps', 'jain', 'cubic_share_pct', 'retrans_pct',
                   'probe_rtt_p50', 'queue_delay_ms', 'max_backlog_pkts', 'udp_loss_pct',
                   'udp_jitter_ms']


def jain(x):
    x = np.asarray(x, dtype=float)
    return x.sum() ** 2 / (len(x) * (x ** 2).sum()) if len(x) > 1 and (x ** 2).sum() > 0 else np.nan


def load(scenario, special=False):
    flows = pd.read_csv(DATA / f'{scenario}_flows.csv')
    trials = pd.read_csv(DATA / f'{scenario}_trials.csv')
    return flows[flows.special == special], trials[trials.special == special]


def per_trial(scenario):
    """One row per (config, trial): utilization, fairness and shares, joined with queue metrics.

    Utilization is the bottleneck's wire rate (tc Sent bytes, headers included) over R, so a link
    that never idles reads ~100%. Goodput tops out lower: ~47.8 Mbps per 50 Mbps for TCP."""
    flows, trials = load(scenario)
    rows = []
    for (config, trial), g in flows.groupby(['config', 'trial']):
        tcp, udp = g[g.kind == 'tcp'], g[g.kind == 'udp']
        rate = g.rate.iloc[0]
        row = dict(config=config, trial=trial,
                   tcp_mbps=tcp.goodput_mbps.sum(),
                   jain=jain(tcp.goodput_mbps),
                   # all TCP flows together: retransmitted / sent, weighted by bytes sent, so a
                   # starved flow with a few segments in the window cannot dominate the mean
                   retrans_pct=(tcp.retrans_pct * tcp.bytes_sent).sum() / max(tcp.bytes_sent.sum(), 1))
        if set(tcp.flow_cca) == {'cubic', 'bbr'}:
            row['cubic_share_pct'] = 100 * tcp[tcp.flow_cca == 'cubic'].goodput_mbps.sum() / tcp.goodput_mbps.sum()
        if len(udp):
            row.update(udp_loss_pct=udp.udp_loss_pct.iloc[0], udp_jitter_ms=udp.udp_jitter_ms.iloc[0])
        rows.append(row)
    keep = ['config', 'trial'] + PARAMS + ['probe_rtt_p50', 'queue_delay_ms', 'max_backlog_pkts',
                                           'drops', 'buffer_pkts', 'wire_mbps']
    df = pd.DataFrame(rows).merge(trials[keep], on=['config', 'trial'])
    df['utilization_pct'] = 100 * df.wire_mbps / df.rate
    return df


def ci95(values):
    """Half-width of the 95% confidence interval of the mean (Student's t)."""
    v = pd.Series(values).dropna()
    if len(v) < 2:
        return np.nan
    return stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))


def summarize(df):
    """Mean, CI half-width and trial count per configuration."""
    out = []
    for config, g in df.groupby('config'):
        row = {'config': config, 'trials': len(g), **{p: g[p].iloc[0] for p in PARAMS}}
        for m in SUMMARY_METRICS:
            if m in g and g[m].notna().any():
                row[f'{m}_mean'] = g[m].mean()
                row[f'{m}_ci'] = ci95(g[m])
        out.append(row)
    return pd.DataFrame(out)


def expected_configs(scenario):
    """Configuration IDs the experiment file defines, so configs with no data at all are caught."""
    import yaml
    from run import load_configs
    spec = yaml.safe_load(next(Path('experiments').glob(f'{scenario}_*.yaml')).read_text())
    return [c['id'] for c in load_configs(spec)]


def check(summary, scenario, expected_trials=5, max_rel_ci=0.10, min_abs_ci=1.0):
    """(config, problem) for missing configurations, missing trials, or a CI wider than 10% of the mean.

    A CI under 1 (Mbps or utilization points, 2% of a 50 Mbps link) is never flagged: a starved
    flow's mean is near zero, so 10% of it is noise more trials cannot remove."""
    problems = [(c, 'no completed trials') for c in expected_configs(scenario)
                if c not in set(summary.config)]
    for _, r in summary.iterrows():
        if r.trials < expected_trials:
            problems.append((r.config, f'only {r.trials} of {expected_trials} trials'))
        for m in ('utilization_pct', 'tcp_mbps'):
            mean, ci = r.get(f'{m}_mean'), r.get(f'{m}_ci')
            if pd.notna(mean) and pd.notna(ci) and mean > 0 and ci / mean > max_rel_ci and ci >= min_abs_ci:
                problems.append((r.config, f'{m} = {mean:.1f} ± {ci:.1f} (CI {100 * ci / mean:.0f}% of mean)'))
    return problems


def convergence(scenario, threshold=0.9, hold=5):
    """Staggered runs: seconds after the last flow joins until Jain's index stays above 0.9."""
    series = pd.read_csv(DATA / f'{scenario}_series.csv')
    series = series[series.run.str.contains('staggered') & (series.kind == 'tcp')]
    results = []
    for (run, config, trial), g in series.groupby(['run', 'config', 'trial']):
        last_join = g.start.max()
        g = g[g.t > last_join].assign(sec=lambda x: np.ceil(x.t))
        j = g.groupby('sec').mbps.apply(jain).sort_index()
        above = (j > threshold).astype(int)
        streak = above.groupby((above != above.shift()).cumsum()).cumsum()
        hit = streak[(streak >= hold) & (above == 1)]
        t_conv = hit.index[0] - hold + 1 - last_join if len(hit) else np.nan
        results.append(dict(run=run, config=config, trial=trial, convergence_s=t_conv))
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('scenario')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--flagged', action='store_true', help='print only the IDs --check flags')
    parser.add_argument('--trials', type=int, default=5)
    args = parser.parse_args()

    summary = summarize(per_trial(args.scenario))
    if args.flagged:
        print('\n'.join(sorted({c for c, _ in check(summary, args.scenario, args.trials)})))
        return
    FIGURES.mkdir(exist_ok=True)
    summary.to_csv(FIGURES / f'{args.scenario}_summary.csv', index=False)
    print(f'{len(summary)} configurations -> {FIGURES}/{args.scenario}_summary.csv')
    if args.check:
        problems = check(summary, args.scenario, args.trials)
        print('\n'.join(f'{c}: {p}' for c, p in problems) if problems else 'all configurations OK')
    series = DATA / f'{args.scenario}_series.csv'
    if series.exists() and pd.read_csv(series, usecols=['run']).run.str.contains('staggered').any():
        print(convergence(args.scenario).to_string(index=False))


if __name__ == '__main__':
    main()

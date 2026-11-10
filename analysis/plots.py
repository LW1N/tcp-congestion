"""Report figures F1-F8 from the parsed CSVs.

  python3 -m analysis.plots          # all figures
  python3 -m analysis.plots F4 F5    # selected figures
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.metrics import DATA, FIGURES, ci95, per_trial, summarize
from topo.shaping import bdp_packets

CCA_COLOR = {'reno': '#0072B2', 'cubic': '#E69F00', 'bbr': '#009E73', 'cubic+bbr': '#CC79A7'}
QDISC_COLOR = {'pfifo': '#555555', 'red': '#D55E00', 'fq_codel': '#56B4E9'}
QDISC_STYLE = {'pfifo': '-', 'red': '-.', 'fq_codel': '--'}
CCAS = ['reno', 'cubic', 'bbr']
plt.rcParams.update({'figure.dpi': 110, 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': 0.3})


def save(fig, name):
    FIGURES.mkdir(exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(FIGURES / f'{name}.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {FIGURES}/{name}.png')


def csv(name):
    path = DATA / f'{name}.csv'
    if not path.exists():
        raise FileNotFoundError(f'{path} missing - run python3 -m analysis.parse first')
    df = pd.read_csv(path)
    return df[~df.special] if 'special' in df else df


def f1_single_flow_cwnd():
    """Window over time for one flow of each CCA, against BDP and BDP + buffer."""
    ss, flows = csv('s1_ss'), csv('s1_flows')
    fig, axes = plt.subplots(3, 1, figsize=(7, 6), layout='constrained', sharex=True)
    for ax, cca in zip(axes, CCAS):
        d = ss[(ss.config == f'n1-{cca}') & (ss.trial == 1)]
        if d.empty:
            continue
        bdp = bdp_packets(d.rate.iloc[0], d.rtt.iloc[0])
        ax.plot(d.t, d.cwnd_pkts, color=CCA_COLOR[cca], lw=1)
        ax.axhline(bdp, color='k', ls=':', lw=1)
        ax.axhline(bdp * (1 + d.buf_bdp.iloc[0]), color='k', ls='--', lw=1)
        gp = flows[flows.config == f'n1-{cca}'].goodput_mbps
        ax.set_title(f'{cca.upper()}: {gp.mean():.2f} ± {ci95(gp):.2f} Mbps', loc='left')
        ax.set_ylabel('cwnd (packets)')
    axes[0].text(1, bdp, ' BDP', va='bottom', fontsize=8)
    axes[0].text(1, bdp * 2, ' BDP + buffer', va='bottom', fontsize=8)
    axes[-1].set_xlabel('time since flow start (s)')
    fig.suptitle('Single-flow congestion window by CCA (50 Mbps, 40 ms, 1× BDP buffer)', x=0.01, ha='left')
    save(fig, 'F1_s1_single_flow_cwnd')


def f2_fairness():
    """Jain's index by CCA mix, for equal and mixed RTTs."""
    s = summarize(per_trial('s1'))
    s = s[s.n > 1]
    mixes = ['reno', 'cubic', 'bbr', 'cubic+bbr']
    combos = [(2, 'pfifo'), (2, 'fq_codel'), (4, 'pfifo'), (4, 'fq_codel')]
    shades = ['#8c8c8c', '#9ecae1', '#3a3a3a', '#2171b5']
    fig, axes = plt.subplots(1, 2, figsize=(9, 2.8), layout='constrained', sharey=True)
    x = np.arange(len(mixes))
    for ax, mode in zip(axes, ['equal', 'mixed']):
        for k, ((n, q), color) in enumerate(zip(combos, shades)):
            d = s[(s.rtt_mode == mode) & (s.n == n) & (s.qdisc == q)].set_index('cca_mix').reindex(mixes)
            ax.bar(x + (k - 1.5) * 0.2, d.jain_mean, 0.2, yerr=d.jain_ci, color=color,
                   capsize=2, label=f'{n} flows, {q}')
        ax.set_xticks(x, mixes)
        ax.set_title(f'{mode} RTTs', loc='left')
        ax.set_ylim(0, 1.05)
    axes[0].set_ylabel("Jain's fairness index")
    fig.legend(*axes[0].get_legend_handles_labels(), loc='outside lower center', ncol=4, fontsize=7)
    fig.suptitle("Fairness between competing TCP flows (mean ± 95% CI)", x=0.01, ha='left')
    save(fig, 'F2_s1_fairness')


def f3_rtt_bias():
    """Share of the link per flow by path RTT, 4 flows with mixed RTTs, pfifo."""
    flows = csv('s1_flows')
    d = flows[(flows.n == 4) & (flows.rtt_mode == 'mixed') & (flows.qdisc == 'pfifo')
              & flows.cca_mix.isin(CCAS)].copy()
    d['share'] = 100 * d.goodput_mbps / d.groupby(['config', 'trial']).goodput_mbps.transform('sum')
    rtts = sorted(d.path_rtt.unique())
    x = np.arange(len(rtts))
    fig, ax = plt.subplots(figsize=(6, 3.4), layout='constrained')
    for k, cca in enumerate(CCAS):
        g = d[d.cca_mix == cca].groupby('path_rtt').share
        ax.bar(x + (k - 1) * 0.27, g.mean().reindex(rtts), 0.27, yerr=g.apply(ci95).reindex(rtts),
               color=CCA_COLOR[cca], capsize=2, label=cca)
    ax.axhline(25, color='k', ls=':', lw=1)
    ax.text(len(rtts) - 0.5, 25.5, 'fair share', ha='right', fontsize=8)
    ax.set_xticks(x, [f'{r:g} ms' for r in rtts])
    ax.set_xlabel('path RTT')
    ax.set_ylabel('share of TCP throughput (%)')
    ax.legend()
    ax.set_title('RTT bias: share per flow, 4 flows with mixed RTTs, pfifo', loc='left')
    save(fig, 'F3_s1_rtt_bias')


def f4_tcp_vs_udp():
    """TCP aggregate goodput, UDP loss and UDP jitter as the UDP rate rises."""
    s = summarize(per_trial('s2'))
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.0), layout='constrained')
    for cca in CCAS:
        for q in ['pfifo', 'fq_codel']:
            d = s[(s.cca == cca) & (s.qdisc == q)].sort_values('udp_pct')
            kw = dict(color=CCA_COLOR[cca], ls=QDISC_STYLE[q], marker='o', ms=3, capsize=2)
            axes[0].errorbar(d.udp_pct, d.tcp_mbps_mean, yerr=d.tcp_mbps_ci, label=f'{cca}, {q}', **kw)
            axes[1].errorbar(d.udp_pct, d.udp_loss_pct_mean, yerr=d.udp_loss_pct_ci, **kw)
            axes[2].errorbar(d.udp_pct, d.udp_jitter_ms_mean, yerr=d.udp_jitter_ms_ci, **kw)
    axes[0].set_ylabel('TCP aggregate goodput (Mbps)')
    axes[1].set_ylabel('UDP loss (%)')
    axes[2].set_ylabel('UDP jitter (ms)')
    for ax in axes:
        ax.set_xlabel('UDP offered load (% of bottleneck)')
        ax.set_ylim(bottom=0)
    fig.legend(*axes[0].get_legend_handles_labels(), loc='outside lower center', ncol=6, fontsize=7)
    fig.suptitle('3 TCP flows vs. 1 UDP flow (solid pfifo, dashed fq_codel)', x=0.01, ha='left')
    save(fig, 'F4_s2_tcp_vs_udp')


def f5_utilization_vs_buffer():
    """Single-flow utilization vs. buffer size, one line per RTT."""
    s = summarize(per_trial('s3'))
    s = s[s.n == 1]
    blues = {10: '#9ecae1', 50: '#4292c6', 150: '#08306b'}
    fig, axes = plt.subplots(1, 3, figsize=(10, 2.7), layout='constrained', sharey=True)
    for ax, cca in zip(axes, CCAS):
        for rtt, color in blues.items():
            d = s[(s.cca == cca) & (s.rtt == rtt)].sort_values('buf_bdp')
            ax.errorbar(d.buf_bdp, d.utilization_pct_mean, yerr=d.utilization_pct_ci, color=color,
                        marker='o', ms=3, capsize=2, label=f'RTT {rtt} ms')
        ax.set_xscale('log', base=2)
        ax.set_xticks([0.25, 1, 4], ['0.25×', '1×', '4×'])
        ax.set_xlabel('buffer (× BDP)')
        ax.set_title(cca.upper(), loc='left')
    axes[0].set_ylabel('utilization (%)')
    axes[0].legend(fontsize=7)
    fig.suptitle('Single-flow utilization vs. buffer size (mean ± 95% CI)', x=0.01, ha='left')
    save(fig, 'F5_s3_utilization_vs_buffer')


def f6_cubic_vs_bbr():
    """How 2 CUBIC + 2 BBR flows split the link, by buffer depth and queue."""
    s = summarize(per_trial('s3'))
    s = s[s.n == 4]
    qdiscs, bufs = ['pfifo', 'red', 'fq_codel'], sorted(s.buf_bdp.unique())
    fig, axes = plt.subplots(1, 3, figsize=(9, 2.7), layout='constrained', sharey=True)
    for ax, q in zip(axes, qdiscs):
        d = s[s.qdisc == q].set_index('buf_bdp').reindex(bufs)
        x = np.arange(len(bufs))
        ax.bar(x, d.cubic_share_pct_mean, color=CCA_COLOR['cubic'], label='CUBIC')
        ax.bar(x, 100 - d.cubic_share_pct_mean, bottom=d.cubic_share_pct_mean,
               color=CCA_COLOR['bbr'], label='BBR')
        ax.errorbar(x, d.cubic_share_pct_mean, yerr=d.cubic_share_pct_ci, fmt='none', ecolor='k', capsize=2)
        ax.axhline(50, color='k', ls=':', lw=1)
        ax.set_xticks(x, [f'{b:g}×' for b in bufs])
        ax.set_xlabel('buffer (× BDP)')
        ax.set_title(q, loc='left')
    axes[0].set_ylabel('share of TCP throughput (%)')
    axes[-1].legend(fontsize=7, loc='lower right')
    fig.suptitle('CUBIC vs. BBR share, 2 + 2 flows at 50 ms', x=0.01, ha='left')
    save(fig, 'F6_s3_cubic_vs_bbr')


def f7_throughput_vs_delay():
    """Every S3 configuration as a point: queueing delay against utilization."""
    s = summarize(per_trial('s3'))
    markers = {'pfifo': 'o', 'red': 's', 'fq_codel': '^'}
    fig, ax = plt.subplots(figsize=(6, 4), layout='constrained')
    for _, r in s.iterrows():
        key = r.cca if r.n == 1 else 'cubic+bbr'
        ax.scatter(r.queue_delay_ms_mean, r.utilization_pct_mean, color=CCA_COLOR[key],
                   marker=markers[r.qdisc], s=30, alpha=0.85)
    for key, color in CCA_COLOR.items():
        ax.scatter([], [], color=color, label=key)
    for q, m in markers.items():
        ax.scatter([], [], color='grey', marker=m, label=q)
    ax.set_xlabel('queueing delay: probe RTT under load − idle RTT (ms)')
    ax.set_ylabel('utilization (%)')
    ax.legend(fontsize=7, ncol=2)
    ax.set_title('Throughput–delay trade-off, all S3 configurations', loc='left')
    save(fig, 'F7_s3_throughput_vs_delay')


def f8_probe_rtt_cdf():
    """Distribution of RTT under load at 4x BDP for each queue discipline."""
    ping, trials = csv('s3_ping'), csv('s3_trials')
    fig, ax = plt.subplots(figsize=(6, 3.6), layout='constrained')
    for q in ['pfifo', 'red', 'fq_codel']:
        cfg = f'n4-b4-rtt50-cubic+bbr-{q}'
        d = ping[(ping.config == cfg) & (ping.t >= 5) & (ping.t <= 60)].rtt_ms.sort_values()
        if d.empty:
            continue
        ax.plot(d.values, np.linspace(0, 1, len(d)), color=QDISC_COLOR[q], label=q)
    idle = trials[trials.config.str.startswith('n4-b4')].idle_rtt_ms.median()
    ax.axvline(idle, color='k', ls=':', lw=1)
    ax.text(idle, 0.02, ' idle RTT', fontsize=8)
    ax.set_xlabel('probe RTT under load (ms)')
    ax.set_ylabel('fraction of samples')
    ax.legend()
    ax.set_title('RTT under load at 4× BDP, 2 CUBIC + 2 BBR flows', loc='left')
    save(fig, 'F8_s3_probe_rtt_cdf')


FIGS = {'F1': f1_single_flow_cwnd, 'F2': f2_fairness, 'F3': f3_rtt_bias, 'F4': f4_tcp_vs_udp,
        'F5': f5_utilization_vs_buffer, 'F6': f6_cubic_vs_bbr, 'F7': f7_throughput_vs_delay,
        'F8': f8_probe_rtt_cdf}


def main():
    for name in sys.argv[1:] or FIGS:
        try:
            FIGS[name]()
        except FileNotFoundError as exc:
            print(f'{name} skipped: {exc}')


if __name__ == '__main__':
    main()

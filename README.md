# TCP Congestion and Network Performance Analysis

CMPE 206 (SJSU) course project. It measures how TCP congestion control algorithms (Reno, CUBIC, BBR) and router queue disciplines (pfifo, RED, fq_codel) affect throughput, fairness and queueing delay on a shared bottleneck link.

Experiments run in Mininet on a dumbbell topology: senders h1-h4 → switch s1 → router r1 → switch s2 → receivers h5-h8. The bottleneck (50 Mbps by default) is r1's egress toward s2, shaped with `tc` (htb plus the chosen queue). Path delay is added with netem. Traffic comes from iperf3, and ping, `ss`, `tc` and tcpdump record what happens during each trial. Captures are inspected in Wireshark.

Three scenarios, 5 trials per configuration:

| Scenario | File | What varies |
| --- | --- | --- |
| S1 competing TCP flows | `experiments/s1_competing.yaml` | flow count, CCA mix, equal vs mixed RTT, queue |
| S2 TCP vs UDP | `experiments/s2_tcp_udp.yaml` | UDP load (25-100% of the link), CCA, queue |
| S3 buffer x delay | `experiments/s3_buffer_delay.yaml` | buffer size (0.25x, 1x, 4x BDP), RTT, CCA, queue |

Main finding: the queue discipline matters more than the CCA. fq_codel was best or tied-best in every tested condition. The full write-up is in `report/main.pdf`.

## Requirements

- Linux (tested on an Ubuntu 26.04 ARM64 VM) with root access
- Mininet 2.3, Open vSwitch, iperf3, iproute2 (`tc`), tcpdump
- Kernel with the `reno`, `cubic` and `bbr` congestion control modules
- Python 3 with `pyyaml`, `pandas`, `numpy`, `scipy`, `matplotlib`
- Wireshark (optional, for viewing captures)

Load BBR and check that all three algorithms are available:

```bash
sudo modprobe tcp_bbr
sysctl net.ipv4.tcp_available_congestion_control   # expect reno cubic bbr
```

## Running

All commands run from the repository root.

**Try the topology by hand** (opens the Mininet CLI):

```bash
sudo python3 -u -m topo.dumbbell --cli --rate 50 --rtt 40 --buf-bdp 1 --qdisc fq_codel
```

**Run a scenario.** Each trial takes about 75 s, so a full scenario takes several hours. Run one scenario at a time, because each trial's cleanup kills all iperf3 processes and resets Mininet.

```bash
sudo python3 -u run.py experiments/s1_competing.yaml --dry-run   # list configs and time estimate
sudo python3 -u run.py experiments/s1_competing.yaml
```

Useful flags: `--only <config-id>` (repeatable), `--trials N`, `--capture` (pcap in every trial), `--resume <results dir>`, `--staggered` (TCP flows start 10 s apart), `--udp-delay S` (UDP joins late). Raw output goes to `results/<scenario>/<run>/<config-id>/trial_<k>/`.

**Analyze.**

```bash
python3 -m analysis.parse s1            # results/ -> data/s1_*.csv  (s1, s2, s3 or all)
python3 -m analysis.metrics s1          # -> figures/s1_summary.csv (means + 95% CI)
python3 -m analysis.metrics s1 --check  # flag configs that need more trials
python3 -m analysis.plots               # figures F1-F8 into figures/
```

`results/`, `data/` and `figures/` are not tracked in git.

**Live demo** (presentation, press Enter to move through each stage):

```bash
sudo python3 -u demo.py
```

**Report.** Build the PDF with [tectonic](https://tectonic-typesetting.github.io/) (or XeLaTeX on Overleaf):

```bash
cd report && tectonic main.tex
```

If a run crashes and leaves bridges or processes behind, clean up with `sudo mn -c`.

## Layout

| Path | Contents |
| --- | --- |
| `topo/` | dumbbell topology and bottleneck shaping |
| `traffic/` | iperf3 flows and measurement probes |
| `run.py` | runs experiment YAML files unattended |
| `experiments/` | scenario grids |
| `analysis/` | parsing, metrics and plots |
| `demo.py` | live presentation demo |
| `helpers/` | shell shortcuts for the Mac and the VM |
| `devtools/gen_fake.py` | synthetic results for testing the analysis without a VM |
| `evidence/` | screenshots and logs from each project step |
| `report/` | final report (LaTeX source, figures, PDF) |
| `notebook.md` | lab notebook |

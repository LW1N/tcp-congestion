# TCP Congestion and Network Performance Analysis

CMPE 206 (SJSU) course project. It measures how TCP congestion control algorithms (Reno, CUBIC, BBR) and router queue disciplines (pfifo, RED, fq_codel) affect throughput, fairness and queueing delay on a shared bottleneck link.

Experiments run in Mininet on a dumbbell topology: senders h1-h4 → switch s1 → router r1 → switch s2 → receivers h5-h8. The bottleneck (50 Mbps by default) is r1's egress toward s2, shaped with `tc` (htb plus the chosen queue). Path delay is added with netem. Traffic comes from iperf3, and ping, `ss`, `tc` and tcpdump record what happens during each trial. Captures are inspected in Wireshark.

Three scenarios, at least 5 trials per configuration:

| Scenario | File | What varies |
| --- | --- | --- |
| S1 competing TCP flows | `experiments/s1_competing.yaml` | flow count, CCA mix, equal vs mixed RTT, queue |
| S2 TCP vs UDP | `experiments/s2_tcp_udp.yaml` | UDP load (25-100% of the link), CCA, queue |
| S3 buffer x delay | `experiments/s3_buffer_delay.yaml` | buffer size (0.25x, 1x, 4x BDP), RTT, CCA, queue |

Follow-up experiments ran later on a second testbed (Ubuntu 26.04 in WSL2 on an x86 PC). Each has its own scenario name, so its data never overwrites S1-S3. Configurations that repeat an original setting check that the two testbeds agree. The RED follow-ups use `ared`, a RED set by a delay target instead of the buffer size (`topo/shaping.py`).

| Follow-up | File | What it adds |
| --- | --- | --- |
| s1w | `experiments/s1w_reno_wsl.yaml` | Reno + CUBIC and Reno + BBR pairs; 5 S1 settings repeated |
| s1x | `experiments/s1x_rtt_swap.yaml` | mixed-RTT pairs in both path orders; 4 S1 settings repeated |
| s1l | `experiments/s1l_long_reno_cubic.yaml` | Reno vs CUBIC with 180 s flows |
| s3w | `experiments/s3w_reno_bbr.yaml` | 2 Reno + 2 BBR across buffer sizes; 1 S3 setting repeated |
| slong | `experiments/slong_steady_state.yaml` | 180 s reruns of three results still changing at 60 s |
| s3q | `experiments/s3q_queue_fill.yaml` | buffer fill at 4x BDP for 4 flows of each algorithm under pfifo, RED and fq_codel; 1 slong setting repeated |
| s1r | `experiments/s1r_red_competing.yaml` | the S1 grid under `ared`, plus BBR on the short path and Reno vs BBR; 2 S1 settings repeated |
| s2r | `experiments/s2r_red_tcp_udp.yaml` | the S2 grid under `ared`; 3 S2 settings repeated |
| s3r | `experiments/s3r_ared_buffer.yaml` | S3's 2 CUBIC + 2 BBR buffer sweep under `ared`; 3 S3 settings repeated |
| s3qr | `experiments/s3qr_ared_queue_fill.yaml` | s3q's deep-buffer fill test under `ared` |
| s1rs, s2rs, s3qrs | `experiments/s1rs_ared_slow.yaml`, `s2rs_ared_slow.yaml`, `s3qrs_ared_slow.yaml` | the Reno and CUBIC runs of s1r, s2r (25% UDP) and s3qr under `ared_slow`: `ared` with the ARED paper's slow queue average instead of tc's fast default. A negative result: after slow start the average stayed above RED's upper threshold, so RED dropped every packet for seconds at a time and utilization fell below `ared`'s. s3qrs was stopped early because 4 Reno flows locked out in every attempt; it holds 2 CUBIC trials and no Reno trials, so `metrics --check` fails for it |

Main finding: the queue discipline matters more than the CCA. fq_codel was best or tied-best on delay and fairness in every tested condition. The full write-up is in `report/main.pdf`.

## Requirements

- Linux with root access (tested on an Ubuntu 26.04 ARM64 VM under UTM, and Ubuntu 26.04 in WSL2 on x86 for the follow-ups)
- Mininet 2.3, Open vSwitch, iperf3, iproute2 (`tc`), tcpdump
- Kernel with the `reno`, `cubic` and `bbr` congestion control modules
- Python 3 with `pyyaml` for the runner (the system Python, since it runs under sudo)
- [uv](https://docs.astral.sh/uv/) for the analysis: `uv sync` installs `pandas`, `numpy`, `scipy` and `matplotlib` from `pyproject.toml`
- Wireshark (optional, for viewing captures)

Load the kernel modules, start Open vSwitch, and check that all three algorithms are available. On WSL2 the modules are not loaded at boot, so repeat this after every restart:

```bash
sudo modprobe -a tcp_bbr sch_htb sch_red sch_fq_codel sch_netem openvswitch
sudo systemctl enable --now openvswitch-switch
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
uv run python -m analysis.parse s1            # results/ -> data/s1_*.csv  (s1, s2, s3, all = s1-s3, or a follow-up name)
uv run python -m analysis.metrics s1          # -> figures/s1_summary.csv (means + 95% CI)
uv run python -m analysis.metrics s1 --check  # flag configs that need more trials
uv run python -m analysis.plots               # figures F1-F8 into figures/
```

`results/` is not tracked in git. `data/` and `figures/` are, so the report numbers can be reproduced without the raw results. Running `analysis.parse` without `results/` present rewrites `data/` from nothing.

**Live demo** (presentation, press Enter to move through each stage). Each second it redraws each flow's rate, the router's queue and the ping RTT, and it writes the router's traffic to `/tmp/demo.pcap`:

```bash
sudo python3 -u demo.py
```

To watch that capture live in Wireshark on the Mac, run `livecap` (from `helpers/mac.zsh`) once the demo reaches stage 1.

**Report.** Build the PDF with [tectonic](https://tectonic-typesetting.github.io/) (or XeLaTeX on Overleaf):

```bash
cd report && tectonic main.tex
```

The preamble needs Times New Roman or TeX Gyre Termes installed as a system font. Without either, the build stops with a fontspec error.

If a run crashes and leaves bridges or processes behind, clean up with `sudo mn -c`.

## Limitations

- One 50 Mbps bottleneck. Bandwidth was not varied, only delay and buffer size.
- BBR version 1, and ECN never negotiated (kernel default `tcp_ecn=2`, no `ecn` flag on RED).
- Two RED settings. `red` (S3, s3q) puts its thresholds at 1/6 and 1/2 of the buffer, so its target delay grows with the buffer. `ared` (s1r, s2r, s3r, s3qr) is Adaptive RED aiming for a 5 ms average queue, fq_codel's target, at any buffer size.
- 60 s flows. Three competition results were still changing at 60 s and were rerun for 180 s (`slong`).
- Emulated links in VMs, whose timing and packet batching differ from real hardware, which matters most for very small buffers.

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

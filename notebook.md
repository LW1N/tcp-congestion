## 2026-10-22 — Steps 1–2: environment and topology

**Environment (E1.1, E1.2)**
- Ubuntu 26.04.1 LTS, kernel 7.0.0-38-generic, 4 vCPUs, 3.3 GiB RAM visible (4 GB allocated in UTM)
- Mininet 2.3.0, iperf 3.20, TShark 4.6.4, iproute2 6.19.0, Open vSwitch 3.7.1, Python 3.14.4
- Available CCAs: reno cubic bbr -> BBR works on the ARM kernel, no cloud VM needed
- `mn --test pingall`: 0% dropped. "No default OpenFlow controller" warning is expected (falls back to OVS Bridge)
- pip blocked by PEP 668 -> installed Python libraries via apt (python3-pandas etc.)

**Topology and shaping (E2.1–E2.3)**
- Bottleneck = s1-eth1. Senders h1–h4 on s1-eth2..5, receivers h5–h8 on s2-eth2..5, probe hp/hr on s1-eth6 / s2-eth6
- Default: htb 50 Mbit, pfifo limit 167p (1x BDP at 40 ms), netem 40 ms on all receiver ports, TSO/GSO/GRO off
- RED, 0.25x BDP: 42 packets -> limit 63000 B, min 10500 B, max 31500 B
- fq_codel, 4x BDP, 150 ms: limit 2500p, netem 150 ms on all receiver ports

**Surprise 1: first ping ~82 ms instead of 40 ms**
- Observed: h1 -> h5 ping min 41.5 / avg 50.7 / max 83.9 ms
- Cause: the first packet waits for an ARP exchange, which crosses the delayed path, so it pays the RTT twice
- Fix: `net.staticArp()` in topo/dumbbell.py start(). Re-captured E2.1–E2.3
- Why it mattered: run.py's idle-RTT check averages 5 pings, so every trial would have failed it

**Surprise 2: pings 0.3–5 ms above the configured delay**
- Observed after fix: min 40.3 / avg 42.3 / max 44.8 / mdev 1.9 ms (target 40 ms); at 150 ms: min 150.6 / avg 153.0 ms
- Likely cause: VM vCPU wake-up latency (not the shaping config). To confirm in Step 3 with `--rtt 0`
- Fix: run.py idle-RTT check now uses the minimum RTT with tolerance max(10%, 2 ms); Step 3 V1 criterion changed to "min within 1 ms, avg <= 43 ms"
- Impact on analysis: none expected. Queueing delay = loaded RTT - measured idle RTT per trial, so the offset cancels
- For the report: mention as an emulation limitation in methodology; matters most for the 10 ms RTT configs in S3

**State at end of session**
- Code commit: 21f13cf, tagged step2-done
- Next: Step 3 validation (start with `--rtt 0` overhead measurement)

Cause (Step 3): with no netem delay (--rtt 0) the path costs min 0.15 / avg 0.82 / max 2.6 ms of VM latency. At 40 ms (V1) the extra is avg 2.7 ms, so about a third is the VM path and the rest is netem releasing packets late


## Methodology:
UDP through the switch-port bottleneck was capped at 48.7 Mbps with 0% loss (60.0 Mbps when bypassing it).
Cause: packets keep their socket ownership across veth + OVS, so the bottleneck queue pushed back on the sender
(would also have capped TCP queues via TCP Small Queues). Fix: bottleneck moved to router r1 (IP forwarding releases ownership).


## 2026-10-22 (later): router rework, fix verified

**Change: bottleneck moved from switch port s1-eth1 to router r1, port r1-eth1** (cause in the Methodology note above)
- New path: s1 - r1 - s2. r1-eth0 10.0.0.254 (sender side), r1-eth1 10.0.1.254 (receiver side). Receivers renumbered to 10.0.1.5-8, hr to 10.0.1.10
- Only r1-eth1's outbound side is shaped (the data direction). ACKs leave through r1-eth0 unshaped; RTT still comes from netem on s2's receiver ports
- E2.1-E2.4 from the first session show the old topology, so they must be re-captured

**Fix check (quick test, not evidence)**: `topo.dumbbell --cli`, default config
- UDP -b 100M h1->h5, 20 s: sender 100 Mbps, receiver 48.5 Mbps, 51% loss (88641/172661); pfifo dropped 88642. The queue now drops instead of pushing back. Before the fix: 48.7 Mbps, 0% loss
- TCP cubic, 30 s: receiver 47.5 Mbps, 26 retransmits. h1->h5 ping during it: min 56.7 / avg 68.7 / max 79.6 ms, so the queue fills (167 packets drain in ~40 ms)
- Idle ping through the router: min 41.1 / avg 43.3 / max 45.0 ms, no ARP spike, so static ARP still works

**Surprise 3: the link delivers ~48 Mbps of data, not 50**
- Observed: UDP receiver 48.5 Mbps, TCP 47.5 Mbps at R = 50
- Cause: htb counts whole frames. tc showed 125191961 B / 84043 pkt = 1490 B per UDP frame carrying 1448 B of data, so 50 x 1448/1490 = 48.6 Mbps. A TCP frame is 1514 B, so its ceiling is 47.8 Mbps
- Fix: utilization = bytes r1-eth1 sent (tc counter, headers included) / (R x time), in analysis/parse.py and metrics.py; goodput reported separately. Step 3 V2 pass changed to receiver 48.6 +/- 1 Mbps
- For the report: methodology note; explains why goodput never reaches 50 Mbps

**Practical note**
- Mininet CLI: paste one command at a time. While a command runs, extra pasted lines go to that command, not to the prompt

**Next**
- Redo Step 2 evidence (E2.1-E2.4), commit and re-tag step2-done
- Step 3 validation; the --rtt 0 run settles Surprise 2's "Likely cause"


## 2026-10-22: Step 3 validation (E3.1-E3.3)
- All checks pass (E3.2). V2: sender 60.0, receiver 48.4 Mbps, 19% loss; V3: backlog 167p, 16789 drops. Router bottleneck confirmed in recorded evidence
- V5 and V8: 47.5 Mbps both runs, 27 retransmits each. That is 99% of the 47.8 Mbps TCP ceiling, and repeatable
- VM overhead (--rtt 0): 0.150 / 0.821 / 2.609 ms
- V7 hung on the first try: the background flow had ended before tcpdump started, so it waited for packets forever. Fixed with timeout and no initial sleep
- V9 first run could not be verified (one-frame top, clients to /dev/null). Rerun: 95.3% idle with UDP at 48.2 Mbps; TCP flows got 25.0 / 6.34 / 1.00 Mbps because manual pasting staggered the starts
- Early look at H4: once UDP joined, the TCP flows were nearly starved (1-6 Mbps)


## 2026-10-22: Step 4 automation (E4.1, E4.2)

**Dry runs (E4.1)**
- S1 35, S2 24, S3 36 configurations x 5 trials = 475 runs, about 9.5 h estimated
- Captured configurations: S1 6, S2 3, S3 7 (trial 1 only)

**Unattended test: n1-cubic x 2 trials (E4.2)**, code commit 19dbfd0
- Both trials complete with no manual steps; trial 1 has both captures (~41 MB each), trial 2 has none by design
- Capture fix (tcpdump -Z root) confirmed: pcaps are written and non-empty
- Results (parsed on the Mac): goodput 47.78 / 47.79 Mbps, utilization 99.9% / 100.0%, 35 / 30 retransmits
- Idle RTT 40.5 / 41.0 ms; probe RTT under load (median) 68.0 / 71.6 ms, so 27-31 ms of queueing delay
- Queue: mean backlog 116 / 129 packets of 167, max 165 / 167, drops 35 / 31. CUBIC keeps the 1x BDP buffer about 70-75% full: bufferbloat is visible in automated runs, not just by hand
- Trial-to-trial agreement within 0.1% on goodput

**Interrupt test**
- Ctrl-C during an n1-reno run: no leftover Mininet processes (grep count 0), no done marker, so the analysis skips it
- Deleted the interrupted folder results/s1/20261023-001621 (cap and trial don't check for done)

**Surprise 4: utilization read 98.8% on a saturated link**
- Cause: the measurement window ran to traffic_end, which includes teardown. TCP clients actually run 65 s (60 s + 5 s iperf3 omit), so ~1 s of idle link diluted the average
- Fix: parse.py ends the window when the last flow ends (start + duration, + omit for TCP). Real trials now read 99.9%
- Not visible in synthetic data; only real trials exposed it

**Capacity**
- Captures are ~40 MB per file (data + ACKs), not 25 MB. Estimated S1-S3 disk use: ~2.8 GB (captures 1.7 GB, ss samples 1.0 GB) vs 4 GB free of 9.8 GB
- Plan: sudo apt clean, df -h ~ before each scenario, stop below 1.5 GB free

**Next**
- tcp-push (parse.py fix), commit + tag step4-done, tcp-pull
- Step 5: S1 (35 configs x 5 trials, about 3.5 h)


## 2026-10-23 S1 started, commit e3d7f8f
**Run (E5 data)**
- Main run results/s1/20261023-002910: 175/175 trials, all first attempt, no FAILED. Trials 72-74 s apart throughout, so the Mac never slept
- Staggered run 20261023-045729-staggered: 3 trials of n2-equal-cubic+bbr-pfifo
- metrics --check: all configurations OK. Every configuration has 5 trials; Step 4's two test trials were replaced by the main run
- Idle RTT across all trials: 40.1-44.6 ms

**H1: single-flow utilization (n1, pfifo 1x BDP)**
- Reno and CUBIC: 99.98% utilization, 47.8 Mbps goodput (the TCP ceiling). BBR: 97.5%, 46.6 Mbps
- Queueing delay: CUBIC 27.9 ms, Reno 22.6 ms, BBR 0.8 ms. Max backlog: CUBIC/Reno 166 of 167 packets, BBR 53
- Probe RTT under load (median): CUBIC 68.2 ms, Reno 63.9 ms, BBR 42.3 ms
- Why: loss-based CCAs grow until the buffer overflows, so they keep it full; BBR paces at the measured bottleneck rate and keeps about one BDP in flight. BBR gives up ~2.5% because ProbeRTT empties the pipe every 10 s

**Window shapes (E5.1)**
- Reno: sawtooth 240-480 KB, one drop about every 10 s. Peak = BDP (250 KB) + full buffer (~250 KB). Rising edges bend slightly: +1 MSS per RTT, but RTT grows as the queue fills
- CUBIC: concave rise, plateau near the previous max (~410 KB), convex probe, loss. The cubic function is visible directly
- BBR: flat at ~250 KB (one BDP), small bandwidth probes every ~0.3 s, drop to near zero every 10 s (ProbeRTT)

**Slow start and loss recovery (E5.2, E5.3, E5.8)**
- E5.2 Stevens: steps ~43 ms apart (one RTT), each about twice the last, until ~300 ms; then a straight slope at link rate
- E5.3: dup ACK #1-#3 then fast retransmit at 2.29 s, followed by SACK-driven retransmits of further holes
- E5.8 Reno expert: ~340 retransmissions, ~335 of them in the first 5 s (slow-start overshoot: window ~950 KB vs ~500 KB the path holds), then ~1 per sawtooth. CUBIC: 39 fast retransmits, ~30 dup-ACK events
- iperf3 reports far fewer retransmits because -O 5 leaves the first 5 s out of its totals. The capture shows what the summary hides
- 231 RSTs at 67 s = teardown (iperf3 closes while data is in flight); 11 "Malformed iPerf3" = snaplen-truncated control packets. Both harmless

**RTT (E5.4)**
- CUBIC: overshoots to 160 ms during slow start, then ~58-65 ms and climbing (whole-run median 68 ms)
- BBR: 41-43 ms, bumps to ~53 ms during bandwidth probes

**H3: BBR vs CUBIC (E5.5, E5.7)**
- pfifo: CUBIC's share is 10.6% (n2 equal), 10.4% (n2 mixed), 3.3% (n4 equal), 1.9% (n4 mixed). Jain 0.50-0.62
- fq_codel: CUBIC's share is 48.7-50.4%, Jain 1.00. E5.5 shows both locked at 25 Mbps
- Why: BBR ignores loss and sends at its bandwidth estimate; CUBIC backs off on every drop the shared FIFO makes. fq_codel gives each flow its own queue, so BBR's sending cannot push CUBIC's packets out
- E5.7 staggered: CUBIC alone holds 50 Mbps for 10 s; BBR joins and takes ~42 Mbps within ~2 s; CUBIC falls to ~9 Mbps and never recovers. Jain mean 0.64, never above 0.9 for 5 s, so convergence_s = NaN in all 3 trials. Not converging is the finding

**H2: fairness and RTT bias (E5.6)**
- Same CCA, equal RTT, pfifo: Jain 0.95-0.99 (fair)
- n4-mixed-reno-pfifo (20/40/60/80 ms): h1 18.0, h2 14.0, h3 7.5, h4 8.4 Mbps (5-trial means; Jain 0.88)
- Why: Reno adds one MSS per RTT, so the 20 ms flow regrows 3-4x faster after each loss
- Not strictly 1/RTT: 60 ms and 80 ms come out about equal (80 ms slightly ahead). Reno has a short-vs-long bias, not a clean ordering
- fq_codel removes most of it: n4-mixed-reno-fq_codel Jain 0.99

**fq_codel trade-offs**
- Queueing delay about 0 ms for every CCA (slightly negative, -1.3 to +0.1 ms: noise around the idle-RTT baseline)
- Reno + fq_codel: utilization only 94.4-94.6% (n2/n4 equal). CoDel drops early and Reno halves its window, so the link sometimes idles. CUBIC and BBR stay at 98-99.7%

**Surprise 5: several BBR flows overflow the buffer**
- One BBR flow: 53-packet max backlog, 0% retransmits. Two BBR flows on pfifo: 167-packet max backlog (buffer full) and 3.6% (equal RTT) / 5.4% (mixed) retransmits; four: 10.8% (equal RTT), 12.6% (mixed)
- Likely cause: each BBR flow probes at 1.25x its share and the probes add up; BBRv1 does not react to loss, so the queue stays full. To check against the literature for the report
- Mixed-RTT BBR on pfifo: Jain 0.80 (n2), 0.74 (n4). Longer-RTT flows win, the opposite of Reno's bias: n2 20 ms 11.7 vs 80 ms 35.1 Mbps; n4 20/40/60/80 ms = 3.2/14.9/10.4/18.5 Mbps (5-trial means). The 20 ms flow is last in every trial; 40 and 60 ms swing widely between trials (2.7-22.1, 4.9-18.1)
- Why: BBR caps in-flight data at ~2x its estimated BDP (bandwidth x min RTT), so a longer-RTT flow keeps more packets in the shared FIFO and takes more of the link. Known BBRv1 issue; cite in the report
- fq_codel removes it: n4-mixed-bbr-fq_codel gives 11.7-12.0 Mbps to every flow

**Practical notes**
- Wireshark Stevens/RTT graphs: check the title shows 10.0.0.1:<port> -> 10.0.1.5:5201; press d to switch direction. I/O graphs: 10 ms interval for window shapes
- VM tshark returned "permission denied" on the pcaps even with sudo and 644 permissions (cause unconfirmed). Workaround: ran E5.8 with the Mac's tshark and copied the files to the VM with scp
- shot moves the newest Desktop screenshot: always take the screenshot first

**Next**
- Commit + tag s1-done, tcp-pull
- Step 6: S2 (TCP vs UDP, 24 configs x 5 trials, about 2.5 h)


## 2026-10-23 S2 started, commit a1cd65f
**Run**
- First attempt ran S2 and S3 in parallel: invalid, deleted. run.py's cleanup() kills all iperf3/tcpdump/ping and runs mn -c before and after every trial, so each run tore down the other's network. One scenario at a time
- Main run results/s2/20261023-062503: 120/120, one retry (udp100-bbr-pfifo trial 4, idle RTT 47 ms), no sleep gaps
- Late-UDP: 20261023-191437-udpdelay20 (cubic-pfifo), 20261023-191808-udpdelay20 (cubic-fq_codel)
- rerun_flagged reran udp100-{bbr,cubic,reno}-pfifo x 8 (20261023-192941); these replace the main run's 5 trials. 131 trials parsed

**Surprise 6: the check could never pass for starved TCP**
- udp100-*-pfifo stayed flagged after 8 trials: TCP 1.9 +/- 0.7, 2.2 +/- 0.4, 2.1 +/- 0.5 Mbps. The CI is tiny in absolute terms but 17-39% of a near-zero mean
- Fix: metrics.check ignores a CI below 1 Mbps / 1 utilization point (2% of the link). S1 and S2 both "all configurations OK"
- Also fixed: rerun_flagged did not re-parse after rerunning, so the next --check read stale CSVs

**H4: UDP vs TCP (3 TCP flows + 1 UDP flow, 5-trial means)**
- TCP total, pfifo: 36.5 / 25 / 13-14.5 / ~2 Mbps at UDP 25 / 50 / 75 / 100% of R
- TCP total, fq_codel: 34-36.5 Mbps at every UDP rate
- pfifo: TCP gets only what UDP leaves. UDP never backs off; TCP halves on every loss in the shared queue. At 100% TCP is starved
- fq_codel: each flow gets its own queue and an equal share, so UDP is held to ~1/4 (~13 Mbps) and TCP keeps ~3/4. UDP loss 0 / 41-50 / 61-67 / 70-75%: the excess is dropped from UDP's own queue
- Queueing delay: pfifo 22-37 ms, fq_codel about 0

**CCA vs UDP (pfifo)**
- UDP 50%: BBR 25.7, CUBIC 25.1, Reno 25.0 Mbps. UDP 75%: BBR 14.6, CUBIC 13.1, Reno 13.4. UDP 100%: all ~2
- BBR holds up slightly better (+1.5 Mbps at 75%) because it ignores loss, but it does not escape starvation
- BBR also hurts UDP: at UDP 25% on pfifo, UDP loss is 5.9% with BBR vs 0.07% with CUBIC/Reno. BBR keeps the queue full and causes drops; loss-based TCP backs off
- Reno on fq_codel is ~2 Mbps below CUBIC/BBR (34.1-34.8): CoDel's early drops halve Reno's window, the same effect as S1

**Late UDP (E6.1, E6.2)**
- pfifo: TCP at 50 Mbps until UDP joins at 20 s, then near zero within ~0.3 s for 40 s. After UDP stops, TCP regrows slowly (small cwnd after repeated losses)
- fq_codel: TCP drops to ~38 Mbps and stays there; UDP is capped at ~13 Mbps
- Capture time is offset ~2 s from traffic time (the capture starts first): UDP appears at ~22 s in the graphs

**Retransmissions (E6.3)**
- pfifo: largest burst is 93 at 19-20 s, before UDP joins: a synchronized loss of all three CUBIC flows. The UDP join burst is 24 at 22-23 s
- After UDP joins, 115 of 545 TCP data packets (21%) are retransmissions: TCP barely sends, and much of what it sends is repair
- fq_codel: steady 1-3 per second, no jump when UDP joins

**Where the drops happened (E6.4, E6.5)**
- pfifo: 11,532 drops. UDP loss only 3.9%: TCP gave up the link, so UDP alone only slightly overruns it
- fq_codel: 154,362 drops, 116,736 of them drop_overlimit (the 167-packet limit; fq_codel then drops from the longest per-flow queue, which is the UDP flow). UDP offered ~200k packets and lost ~74%, so nearly all drops are UDP's
- UDP jitter: pfifo 0.06 ms, fq_codel 0.24 ms. Both small; fq_codel's round-robin adds a little

**Utilization oddity explained**
- udp100-*-pfifo reads 95-96%, not ~100%. UDP runs 60 s but TCP runs 65 s (iperf3 -O 5). Starved TCP needs several seconds to regrow after UDP stops, so the link is partly idle in the last 5 s of the window (E6.1, 62-65 s)
- Report it as a measurement-window effect, not lost capacity

**Practical notes**
- E6.3 run with the Mac's tshark (VM tshark cannot read the pcaps), copied with scp


## 2026-10-23 S3 started, commit 06739d6
**Run**
- Main run results/s3/20261023-222128: 180/180, no FAILED, no sleep gaps
- 4 idle-RTT retries (5-6 ms over at 50 ms, 2.6 ms over at 10 ms), all passed on attempt 2: VM latency spikes, as in Surprise 2
- rerun_flagged reran n1-b0.25-rtt150-reno x 8 (20261024-022002). 183 trials parsed, "all configurations OK"
- Largest buffer confirmed: n1-b4-rtt150-cubic backlog reached 2500 of 2500 packets
- Bug found: maxbacklog helper still unpacked 3 values after parse_qdisc gained sent bytes (Surprise 3 fix). Fixed, E7.5 rerun

**H1: utilization vs buffer size (single flow; utilization % at RTT 10 / 50 / 150 ms)**
- 0.25x BDP: Reno 22.8 / 86.7 / 82.3, CUBIC 23.6 / 98.2 / 98.5, BBR 97.4 / 96.6 / 95.4
- 1x and 4x BDP: Reno and CUBIC 99.7-100 at every RTT; BBR 96.4-98.5 (ProbeRTT costs ~2-3%)
- Reno at 0.25x: halves to ~186 KB, well below the 312 KB BDP at 50 ms, so the link idles until the window regrows (E7.2)
- CUBIC at 0.25x: backs off only to 0.7x (~262 KB), stays near BDP, keeps ~98%. Its window growth depends on time since the last loss, not on RTT, so it does not slow down at 150 ms
- Reno at 150 ms: 82.3 +/- 5.5% (flagged, 8 trials). Reno grows 1 MSS per RTT, so after halving it needs tens of seconds to regrow; a 60 s trial holds only 1-2 sawtooth cycles, and utilization depends on where the losses fall
- So the shallow-buffer penalty grows with RTT for Reno, not for CUBIC

**Surprise 7: 11-packet buffer collapses loss-based TCP**
- 0.25x BDP at 10 ms = 11 packets. Reno and CUBIC reach only 23% utilization; cwnd median 11 packets vs a 42-packet BDP; ~1100 (Reno) / ~840 (CUBIC) drops per trial
- BBR in the same setup: 97%
- Why: Reno and CUBIC send unpaced bursts that overflow an 11-packet queue before the 50 Mbps link drains it; BBR paces its packets. Matches the small-buffer literature (tiny buffers need smooth traffic)
- Caveat for the report: VM scheduling and netem release packets in batches, which likely makes bursts larger than on real hardware. Present as a trend, not an exact number

**H5: bufferbloat (single flow, queueing delay in ms at RTT 10 / 50 / 150)**
- CUBIC 1x BDP: 4.6 / 34.7 / 105.4. CUBIC 4x BDP: 34.5 / 162 / 494
- Reno 4x BDP: 28 / 127 / 245
- BBR: under 3 ms at every buffer and RTT
- Loss-based CCAs fill whatever buffer exists, so queueing delay scales with buffer size. At 4x BDP and 150 ms, CUBIC's median probe RTT is 646 ms against a 150 ms base
- E7.1: CUBIC's RTT sawtooth runs 175-250 ms (50 ms + up to 200 ms of queue). BBR stays near the 50 ms base (median probe RTT 52 ms). The ~500 ms spikes at each CUBIC loss are Wireshark's RTT for segments waiting behind a hole, not real path delay

**H3: CUBIC vs BBR by buffer depth (2 CUBIC + 2 BBR, 50 ms, pfifo)**
- CUBIC share: 1.4% at 0.25x, 1.8% at 1x, 58.9% at 4x
- Shallow buffer: BBR's paced sending fills the small queue and causes the losses CUBIC reacts to; BBR ignores them (E7.3, CUBIC near zero)
- Deep buffer: CUBIC grows into the 834-packet queue. The queue inflates RTT, and BBR's in-flight cap is tied to its minimum RTT, so it cannot claim the queue. In E7.3 at 4x, CUBIC leads for ~20 s, then BBR recovers and the shares swing back and forth
- Retransmissions follow the buffer: 13.3% at 0.25x, 6.9% at 1x, 0.2% at 4x

**Queue disciplines at 4x BDP (E7.4, E7.5)**
- pfifo: queueing delay 164 ms, max backlog 833 of 834, only 38 drops. The deep buffer almost never overflows, so it stays full
- RED: 48 ms, backlog 323, 368 drops. Early random drops cut the delay, but CUBIC's share stays at 2.5%: the drops hit both CCAs, only CUBIC backs off, and BBR ignores them
- fq_codel: about 0 ms, backlog 299 (brief bursts across flow queues), 0 drops in the sampled trial, CUBIC share 48.3%, Jain 1.00
- fq_codel is the only queue that gives both low delay and fairness. RED fixes delay but not fairness; pfifo fixes neither

**Report notes**
- Where utilization drops: only at 0.25x BDP, for Reno (all RTTs) and CUBIC (10 ms only). BBR is flat at 95-98% everywhere
- Engineering takeaway: deep buffers are needed for loss-based TCP at high utilization, but they add bufferbloat; fq_codel removes the trade-off


## 2026-10-24: Step 8 analysis (E8.1-E8.3)

**Figures (E8.1)**
- F1-F8 generated from one block (parse all, metrics --check x3, plots); all three checks "all configurations OK"
- Fixed after review: F4 had no UDP jitter panel (a required metric), now 3 panels (goodput, loss, jitter). F1 titles showed "± 0.0" (CI ~0.03 rounded); now 2 decimals
- F1 note for the caption: BBR's cwnd sits at ~2x BDP, but its data in flight stays near 1x BDP (E5.1). BBR uses cwnd as a cap, not as its sending rate

**New finding from F4: UDP jitter**
- pfifo: jitter falls to ~0.03 ms as the UDP rate rises. With the queue always full, UDP packets leave at a steady rate
- fq_codel: jitter rises to 0.6-1.1 ms at UDP 75-100%. Round-robin between per-flow queues interleaves UDP with TCP, so UDP packet spacing varies
- Trade-off for the report: fq_codel protects TCP's throughput but costs UDP a little jitter (still about 1 ms)

**Verdicts (E8.3, full table in the plan's Step 8)**
- H1 partly supported: >96% for every CCA at 1x BDP and above; at 0.25x Reno 82-87%, CUBIC ~98%, BBR 95-97%, as predicted. Not predicted: 23% for Reno/CUBIC at 10 ms (11-packet buffer, burst losses; VM batching likely exaggerates)
- H2 supported: equal RTTs Jain 0.95-1.00; Reno favours the 20 ms flow more than CUBIC does (37.7% vs 29%). BBR reverses the bias (80 ms flow 39%, 20 ms flow 7%)
- H3 supported for pfifo: CUBIC's share 1.4% / 1.8% / 58.9% at 0.25x / 1x / 4x BDP. RED keeps BBR dominant at every depth; fq_codel 48-50% everywhere
- H4 supported: UDP at 100% leaves TCP ~2 Mbps on pfifo; fq_codel keeps TCP at 34-36 Mbps at every UDP rate
- H5 supported for CUBIC (adds 80-86% of the 4x BDP drain time), partly for Reno (40-70%, its halving drains the buffer each cycle). BBR <3 ms, fq_codel ~0, RED 48 ms

**Surprises across the project (for report section 7)**
1. Switch-port bottleneck pushed back on senders (skb ownership across veth/OVS): moved to router r1
2. Pings 0.3-5 ms above configured delay: VM latency (~0.8 ms) plus netem release timing
3. Goodput tops out at ~47.8 Mbps, not 50: htb counts frame headers. Utilization measured on the wire
4. Utilization window included teardown: ends when the last flow ends
5. Several BBR flows overflow the buffer (n4 pfifo retransmits 11-13%)
6. Relative CI meaningless for starved TCP: absolute floor added to --check
7. 11-packet buffer collapses loss-based TCP; paced BBR unaffected

**Engineering recommendations (draft for report section 8)**
- Use fq_codel wherever possible: low delay, fair across CCAs and RTTs, protects TCP from UDP. Its only cost seen here is ~1 ms of UDP jitter and a ~2 Mbps (~5%) loss for Reno
- With a plain FIFO: shallow buffers favour BBR and starve CUBIC; deep buffers bring hundreds of ms of bufferbloat. Neither size is safe for mixed CCAs
- RED cuts delay but does not fix BBR-vs-CUBIC unfairness
- Loss-based TCP needs ~1x BDP of buffer for full utilization; with very small buffers, paced senders (BBR, or fq pacing) are required


## 2026-10-24: Step 9 report review, S2 window fix

**Surprise 8: S2's TCP numbers included 5 s without UDP (F18)**
- Observed: per-second iperf3 data shows TCP beside 100% UDP on pfifo at 0.05-0.09 Mbps while UDP runs, but the summary said ~2 Mbps
- Cause: the UDP client has no -O, so it runs 0-60 s; TCP runs 0-65 s and iperf3 summarizes 5-65 s. In the last 5 s TCP has the link to itself and regrows to 25-29 Mbps, and that tail made up most of the "2 Mbps"
- Fix: analysis/parse.py measures every metric over the window in which all flows run (5-65 s; 5-60 s in S2). A flow measured longer than the window is recomputed from its per-second intervals, receiver side from the server JSON. S1 and S3 summaries are unchanged apart from retransmission % (see the F19 bug below); the VM re-run matched the Mac to 1e-12
- New S2 numbers (TCP total, CUBIC, pfifo): 35.5 / 23.1 / 10.7 / 0.05 Mbps at UDP 25 / 50 / 75 / 100% (were 36.5 / 25.1 / 13.1 / 2.2). Reno and BBR within 0.9 Mbps. fq_codel: 35.1-35.4 Mbps (Reno 33.2-33.9)
- udp100-*-pfifo utilization is now 99.8-99.9% (was 95-96%): the "utilization oddity" in the S2 entry was the same tail, not lost capacity
- UDP jitter is now the mean of the per-second values inside the window: fq_codel 0.6-0.8 ms at 75-100% UDP; pfifo 0.04-0.11 ms at 75-100% and 0.17-0.28 ms at 25%

**Why S2 now fits a simple model**
- On pfifo TCP gets exactly the capacity UDP leaves. UDP sends p% x 50 Mbps of payload in 1200 B datagrams, which are 1242 B frames, so UDP's wire rate is 1.035 x p% x 50 Mbps and TCP goodput = (50 - UDP wire rate) x 1448/1514
- Predicted 35.4 / 23.1 / 10.7 / 0 Mbps vs measured 35.5 / 23.1 / 10.7 / 0.05. At 100%, UDP alone needs 51.75 Mbps, 3.4% more than the link carries, which matches its 3.6% loss

**Model checks added for H1 and H5**
- H1: with b BDPs of buffer, cwnd peaks at (1+b) BDP. Reno halves it and grows back linearly, and the link idles while cwnd < 1 BDP. b = 0.25 predicts 89% utilization (measured 86.7% at 50 ms); CUBIC's 0.7x cut predicts ~98% (measured 98.2%)
- H5: Reno cycling between 2.5 and 5 BDP keeps a 4x BDP buffer ~69% full on average; measured 71% at 10 ms and 64% at 50 ms. At 150 ms Reno never regrows within 60 s after its first loss (41%)
- 11-packet buffer: BBR had ~9,500 qdisc drops per trial and still kept 97% (it paces and ignores loss); Reno ~1,100 and CUBIC ~840 drops with 23%

**Bug: retransmission percentages (F19)**
- s2_summary showed retrans_pct up to 2,365,104% for udp100-*-pfifo: the metric averaged per-flow ratios, and a starved flow sends almost no bytes in the window
- Fix: analysis/metrics.py weights each flow by bytes sent (= total retransmitted / total sent). S1 4-flow BBR on pfifo: 10.6% / 10.5% (equal / mixed RTT), was 10.8% / 12.6%

**Corrections to earlier entries**
- S1 E5.7: after BBR joins, CUBIC runs at ~5.1 Mbps (per-second data, all 3 trials). The ~9.3 Mbps figure is the whole-run mean, which includes the seconds before BBR joins
- S1 H2: Reno's 20 ms flow regrows ~2.2x faster than its 80 ms flow, not 3-4x: the effective RTTs include ~29 ms of queueing (49 vs 109 ms)
- S2 CCA vs UDP: BBR's advantage over CUBIC is at most 0.9 Mbps (was +1.5 Mbps at 75%); BBR's UDP loss at 25% is 5.8% (was 5.9%)
- Step 8 verdicts: H4 now reads "TCP < 0.1 Mbps beside 100% UDP"; fq_codel jitter 0.6-0.8 ms (was 0.6-1.1); H5's Reno mechanism is the 2.5-5 BDP cycle above, not "drains the buffer each cycle"

**Report (Step 9)**
- Cut from 22 to 8 pages (Docs PDF export, letter): 6 figures (topology, F2, F4, F5, F6, E6.1 annotated), 3 tables (scenarios, verdicts, recommendations); references 1-16 checked online
- Figures regenerated: no "Fn." prefix in titles (report numbering differs), F2 legend moved below the plot, shorter plot heights
- E9.1: evidence/step9-report/E9.1_report.pdf (Mac only; evidence/ is not pushed)

**Practical notes**
- tcp-push does not copy notebook.md, and tcp-pull overwrites the Mac copy from the VM. This notebook was repaired on the Mac (12 passages lost text during heredoc pastes) and copied back to the VM with scp
- The Docs PDF export prints LaTeX code blocks as raw source, so the report's formulas are inline text

**Next**
- Step 10: slides from the report, rehearse demo.py twice, E10.2 recording, E10.3 transcript

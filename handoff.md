# handoff.md: agent handoff for CMPE 206 TCP congestion project

<!--
Format: optimized for AI agents. Facts are key: value lines or tables with exact identifiers.
Status values: DONE | TODO | IN_PROGRESS | UNVERIFIED | UNKNOWN. UNVERIFIED = implemented but never observed
working where it matters. UNKNOWN = ask the user or check before relying on it.
Last updated: 2026-11-15 (after the accuracy review: F26-F30, report f35ad61, deck v262, guide v26, demo upgrade a859ed1).
-->

## 0. READ_FIRST

1. Read this file, then `requirements.md` (course requirements: report sections, 6-8 pages, rubric 20/20/20/20/10/10).
2. Code and docs are edited on the user's Windows PC in WSL2 (`/home/lucas/tcp-congestion`). The live demo runs on the Mac + VM (decided 2026-11-15): code reaches the VM via GitHub -> Mac `git pull` -> `tcp-push`. Claude cannot run sudo; the user runs experiments and demo.py and pastes output.
3. Deliverables: report `report/main.pdf` (8 pages, section 4c), slide deck (4b, 16 slides), prep guide (4d). Experiments are finished; all data is in git.
4. Before editing the deck or guide, re-read them (Artifact read): a publish overwrites edits the user made in the editor (F24).
5. Highest priority: OPEN_ITEMS #1 (user steps through deck version 262 in Present mode; no slide has ever been rendered) and #2 (dry-run the upgraded demo.py with livecap on Mac + VM; never run).
6. Prose rules: R12, R14 (user's voice). Slide rules: R13. Do not trust UNKNOWN items (section 9 lists them).

## 1. USER_RULES (must follow)

- R1: Every command complete and copy-pasteable. No placeholders, no "see above".
- R2: Label where each code block runs: `# WSL` (current), `# Mac`, `# VM`, `# mininet>`. Several commands meant to run in order each get their own block.
- R2a: Mininet CLI commands: one per block (Mininet forwards later pasted lines to stdin).
- R3: Prefer helper shortcuts (section 6) where they exist (Mac/VM only).
- R4: SUPERSEDED 2026-11-15. Code used to live on the Mac and reach the VM via `tcp-push`; the WSL repo is now the working copy, pushed to GitHub by the user.
- R5: When the user pastes terminal output, check it against expectations and look for anomalies (found F9-F14, F21, F22 this way).
- R6: Refer to the user with they/them.
- R7: After code changes run local checks (section 9) and a Sonnet subagent review of the diff (user's global CLAUDE.md).
- R8: notebook.md canonical copy was on the VM; give entries as heredocs, never overwrite blindly. Which copy is canonical now that work moved to WSL is UNKNOWN (open item 7).
- R9: Notebook entries hold measured numbers, mechanisms, numbered Surprises, practical notes, Next.
- R10: The VM is shared; never assume it is up or clean (bring-up block in section 3).
- R11: Use exactly the host form the user asks for in commands (they once asked for `lucas@vm0.local` instead of `tcpvm`).
- R12: Deliverables must not read as AI-generated: varied sentence openings and lengths, no aphoristic 'Label: claim.' openers, some first person, exact numbers.
- R13: Slides: few on-slide words (~25), visuals and animations preferred, details in speaker notes (<aside>), no H1-H5 labels or config ids on slides, define CCA, RTT, BDP, Jain where first used, easy for an audience seeing it once.
- R14: Prose in the user's voice: reason-first openings, 'This ...' follow-ups, plain words, first person, no semicolons or em dashes. Sample: paragraphs 4-5 of `CMPE 272 Group Reflection.pdf` (on the Mac); memory file user-writing-voice.md lives in the Mac session memory dir, not here.
- R15: Report: two-column IEEE, Times New Roman, 12 pt, 6-8 pages (keep at 8).
- R16: Do not start experiment runs unless asked ("DO NOT RUN" when preparing); prepare files and give run commands.
- R17: The user commits with messages Claude drafts (`/commit-message`, no Co-Authored-By trailer). Give multi-line messages as `git commit -F - <<'EOF' ... EOF`; quoting them with -m broke once (F25).
- R18: Hedge mechanisms that were not measured ("likely", "consistent with"); state cross-machine comparisons as such.

## 2. PROJECT

```yaml
user: Lucas Nguyen (solo)
course: CMPE 206, SJSU; option: TCP Congestion and Network Performance Analysis; tools: Mininet, iperf3, Wireshark
scenarios: {S1: competing TCP flows + single-flow baseline, S2: 3 TCP + 1 UDP, S3: buffer (router queue size) x delay}
dropped: [random-loss scenario, bandwidth sweep (bandwidth fixed at 50 Mbps), parking-lot topology (future work)]
axes: {cca: [reno, cubic, bbr v1], qdisc: [pfifo, red, fq_codel], buffer_x_bdp: [0.25, 1, 4], rtt_ms: [10..150]}
main_study (VM): {configs: 95, trials: 492, run: 2026-10-23..24, tag on VM: s3-done}
follow_ups (WSL, own scenario names): {configs: 29 (23 S1, 6 S3), trials: 145, calibration: 10 configs repeat VM settings, CIs overlap except 5 small gaps (largest 10 ms / 5% loaded RTT at 4x BDP)}
framing: loss-based (Reno, CUBIC) vs model-based (BBR v1) vs unresponsive (UDP); results follow that split
headline: the router queue matters more than the CCA; fq_codel best or tied-best on delay and fairness everywhere
schedule: {submission: 2026-12-11 ASSUMED (UNKNOWN), report submitted: UNKNOWN}
```

Hypotheses (proposal) and verdicts: H1 utilization at >=1x BDP: PARTLY (11-packet buffer at 10 ms collapses Reno/CUBIC to 23%). H2 Reno favors short RTT more than CUBIC: SUPPORTED, BBR favors long RTT. H3 BBR wins shallow buffers, CUBIC recovers in deep: SUPPORTED on pfifo; deep (4x BDP) settles at an even split (F22); RED keeps BBR on top. H4 line-rate UDP starves TCP, fq_codel fixes it: SUPPORTED (0.05 -> 35 Mbps). H5 deep FIFO adds its drain time: CUBIC yes (80-86% full), Reno partly (64-71%, 41% at 150 ms).

Key numbers (main study, pfifo unless noted): single flow util Reno/CUBIC 99.98/99.97%, BBR 97.5%; queue delay CUBIC 27.9, Reno 22.6, BBR 0.8 ms; CUBIC vs BBR 1+1 same RTT 10.6%, 2+2 1.9-3.3%, fq_codel 48-50%; S3 2+2 CUBIC 1.4 / 1.8 / 58.9% at 0.25/1/4x (60 s; settles ~51% at 4x); 4x BDP single-flow delay CUBIC 34.5/162/494 ms, Reno 28/127/245 at 10/50/150 ms; S2 pfifo TCP 35.5/23.1/10.7/0.05 Mbps at UDP 25-100%, fq_codel ~35.

| follow-up (scenario, file) | result (share of the loss-based CCA) |
| --- | --- |
| s1w `experiments/s1w_reno_wsl.yaml` | Reno vs BBR equal 40 ms: 10.0% pfifo, 43.8% fq_codel; Reno vs CUBIC 60 s 47.9 +/- 11% (inconclusive) |
| s1x `experiments/s1x_rtt_swap.yaml` | path order swapped (F21): CUBIC on 80 ms vs BBR on 20 ms 46.8% (10.4% other order); Reno 55.6% vs 12.7%; 2+2 BBR wins either order (1.8 / 2.9%) |
| s1l `experiments/s1l_long_reno_cubic.yaml` | Reno vs CUBIC 180 s: Reno 38.0 +/- 4.1% (~49% first 30 s, then 34-37%) |
| s3w `experiments/s3w_reno_bbr.yaml` | 2 Reno + 2 BBR: 1.9 / 2.3% at 0.25/1x; 4x: 55.3% at 60 s |
| slong `experiments/slong_steady_state.yaml` | 180 s reruns (F22), settled 65-185 s: CUBIC vs BBR 4x 51.1 +/- 1.1%; Reno vs BBR 4x 48.1 +/- 1.5%; BBR 20 ms vs CUBIC 80 ms 47.0 +/- 7.9% |

## 3. ENVIRONMENT

```yaml
wsl_pc (current):
  host: Windows PC, AMD Ryzen 5 5600X, 15 GB RAM; Ubuntu 26.04.1 in WSL2, kernel 6.18.58.1-microsoft-standard-WSL2, systemd on
  repo: /home/lucas/tcp-congestion (origin https://github.com/LW1N/tcp-congestion, PUBLIC); main == origin/main at a859ed1 (2026-11-15)
  apt: {mininet: 2.3.0-1.1build1, openvswitch-switch: 3.7.1-2, iperf3: 3.20-2, tcpdump: 4.99.6-1, iproute2: 6.19.0}
  python: system 3.14.4 (has yaml; runner runs under sudo with it); analysis via uv 0.13.7 (~/.local/bin/uv, pyproject.toml + uv.lock, .venv/)
  latex: tectonic 0.17.0 (~/.local/bin); needs Times New Roman via fontconfig (F23)
  modules: not loaded at boot; after every WSL restart run the bring-up below
  raw_results: results/{s1w,s1x,s1l,s3w,slong} 478 MB, gitignored, only on this PC (no backup)
  limits: sudo needs the user's password; no node/JS engine; pip/uv installs of JS tools (esprima, quickjs) denied by the auto-mode classifier; Claude in Chrome not connected (list_connected_browsers empty, no render checks); JS checked only by a bracket/string tokenizer (was <scratchpad>/jstok.py, may be wiped); root-owned __pycache__ in topo/ traffic/ from sudo runs (harmless)
  scratchpad: /tmp/claude-1000/-home-lucas-tcp-congestion/<session>/scratchpad, wiped on WSL restart
bring_up_wsl: "# WSL: sudo modprobe -a tcp_bbr sch_htb sch_red sch_fq_codel sch_netem openvswitch && sudo systemctl enable --now openvswitch-switch && cat /proc/sys/net/ipv4/tcp_available_congestion_control   (expect reno cubic bbr)"
mac (demo machine): Apple M2, zsh, repo ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion (update with git pull); holds results/ 2.6 GB of the main study (46 pcaps); Wireshark + tshark; Wireshark binary assumed at /Applications/Wireshark.app/Contents/MacOS/Wireshark (UNVERIFIED)
vm (original testbed, demo host): UTM, Ubuntu 26.04.1 ARM64, kernel 7.0.0-38-generic, 4 vCPU, 3.3 GiB; host vm0, user lucas, alias tcpvm; ~/tcp-congestion; 1.4 GB free; same tool versions as WSL; tcp_bbr autoloads
vm_bring_up: ["# Mac: ssh tcpvm 'echo connected to $(hostname)'", "# VM: cd ~/tcp-congestion && sudo -v && sudo mn -c"]
```

## 4. DOCS (Claude Docs on claude.ai)

| key | url | project_id | body_node_id | last_known_rev | status |
| --- | --- | --- | --- | --- | --- |
| proposal | https://claude.ai/artifact/MHnQC8nYRexNPwSauG9wwK | a44ea6f5-2c85-42dd-80ed-b60386cd4e56 | a6564636-68fa | 65 | submitted |
| guide (implementation plan) | https://claude.ai/artifact/BokvUU7o8zuiJZKsWbbiRN | 5782aafa-bbcf-41e2-8797-79b73db5ec59 | 80b14e81-2d18 | 153 | stale: Mac/VM era, no follow-ups, says .gitignore excludes data/ and figures/ (tracked since 1539d5d) |
| report doc | https://claude.ai/artifact/7vJiBvAn1QoxLYNaCXatnG | 38082a81-1bd5-4de3-9460-1437f9709115 | 26792df3-7a2c | 69 | SUPERSEDED by report/main.tex |

Doc quirks: read changes since last rev before editing (`read(ref node <body_node_id>, payload {"kind":"view","sinceRev":<rev>})`); whole-block replace needs ifHash + ifRev; guide evidence chips: replace the cell (table mj7hsvwewd5.50640, col 5, enum f2528a45-54f5).

## 4b. SLIDE DECK (Slides artifact)

```yaml
url: https://claude.ai/artifact/2GZMMEVvtSyVmNHZ44rzys   # private until the user shares it
type_url: https://claude.ai/artifact/8jTsAFQMFDb2oA8MsPJ2eL (contract 0.2.47)
last_published: 1794808871-4524 (version 262, 2026-11-15; v256 copies kept in <scratchpad>/deck-v256-backup until wiped)
order: [cover, problem, compare, topology, implementation, scenarios, renocubic, s1, s2, capture, s3share, s3delay, verdicts, recommendations, demo, close]
numbering: footer 'n / 16' (none on cover/close), eyebrow 'NN ·' = n-1 (01-15), progress bar width 104*n px at top 1040
local_copy: <scratchpad>/deck-rc/project (publish root <scratchpad>/deck-rc); may vanish -> Artifact read with paths project/deck.json, project/slides/<id>.html
publish: Artifact publish url=<deck>, root=<copy root>, file_path=<changed slide>, files={"project/slides/<id>.html": ...}; include project/deck.json when order changes
style: Capture Dark (bg #111019, card #1C1B27, text #F4F3F7, muted #A9A7BB, footer #8A889C); queues amber pfifo #FFB23E, violet RED #A78BFA, cyan fq_codel #4FD1E0; slide 7 algorithms Reno #A78BFA, CUBIC #4FD1E0, BBR #FF5C8A; drop #FF6B6B; fonts Schibsted Grotesk + IBM Plex Mono
slides_of_note:
  3 compare: chips 'loss-based' (Reno, CUBIC) and 'model-based' (BBR) at top 470; BBR caption 'paces to bandwidth, not loss'; notes explain bandwidth + min RTT model and ~2x in-flight cap; fq_codel drops drawn red
  7 renocubic: 'Reno trails CUBIC. Against BBR, both lose'; left panel 'Same family: CUBIC ahead'; two x-embed toy sketches (dashed link, grey total, red loss) + measured bars Reno 38 / CUBIC 62*, CUBIC 11 / BBR 89, Reno 10* / BBR 90; JS UNVERIFIED (never executed)
  8 s1: 5 rows at 118 px, 15 px per %; swapped-path row 46.8/46.9* (label inside the amber bar); side card 'delay added on the FIFO' 27.9 (1 CUBIC) / 0.8 (1 BBR) / 37–40 ms (2–4 BBR, red) + grey '2–4 CUBIC flows: 32–34 ms'
  11 s3share: pfifo 4x bar = solid 51%* (settled, slong) inside dashed 59% outline (first minute), note 'dashed = 1st minute'; RED card 'BBR still wins'; card 'At 4× BDP: about even', 'Reno*: same pattern'
  6 scenarios: S2 sketch drops packets from every flow (30%), only TCP halves; line 'Reno, CUBIC, BBR on pfifo and fq_codel (S3: fq_codel only with 4 flows) · RED in S3'
  13 verdicts: H1 '≥ 1× BDP keeps the link busy; 0.25× costs Reno 10–15%' / 'Partly · 0.25× at 10 ms fell to 23%'; H3 'Yes on pfifo · large = even split'; H5 'Partly · CUBIC 81–86% of it, Reno 41–71%'
  12 s3delay: 4 mixed flows 164 / 48 / '≈ 10 ms*' (fq_codel = TCP flows' own RTT; footer says a new flow waits ≈ 0)
  14 recommendations: FIFO boxes 'Small: BBR* keeps it busy, Reno doesn't' / 'About 1×: 25–40 ms with 2–4 flows, any algorithm' / 'Large: shrink it (CUBIC adds up to 494 ms)'; footer '*tested alone; beside CUBIC or Reno, BBR takes ~90%'
  15 demo: stage 6 'Wireshark' / 'loss → resend'; caption 'Live: each flow’s rate · the router’s queue · ping RTT · Wireshark I/O graph'; notes give expected ping 68 -> 40 ms
  16 close: fq_codel card 'fair everywhere, delay under 12 ms'
animations: x-embed canvases on slides 1, 2, 3 (x2), 4, 6 (x3), 7 (x2), 12; frozen in PDF/PPTX export, not in Google Slides
embed_rules: no '<' or '&' in embed JS, <= 16 KB each, direct pinned child of <section>, canvas text >= 24 px; <= 200 elements per slide
render_check: NONE ever done (OPEN_ITEMS 1)
```

## 4c. FINAL REPORT (LaTeX, live deliverable)

```yaml
source: report/main.tex   # IEEEtran conference 12pt letter; fontspec Times New Roman, fallback TeX Gyre Termes
output: report/main.pdf   # 8 pages, page 8 full (bottom y 716.2 of 736); committed in f35ad61
build_wsl: see F23; check pages with the scratch venv (pymupdf): page_count must be 8
page_budget: none left; one extra abstract line pushes figures to a 9th page; trade text when adding
content_2026-11-15 (2nd pass, F26/F27): abstract 'added delay under 12 ms', Table III rows (~1x BDP: no CCA fixes delay; deep: shrink; flows' delay <=12 ms), H5 adds multi-BBR vs CUBIC/Reno delay and probe-vs-flow delay under fq_codel, conclusion reworded; trims kept 8 pages (bottom y 716.2)
content_2026-11-15: follow-ups in Platform, Table I caption (29 configs, 145 trials), S1 swap + 180 s, S3 Reno + 180 s head start, H3 'even split', limitations caveat (mostly 60 s flows, no ECN, one RED setting)
not_in_report: negative queue-delay explanation (did not fit; in prep guide Q&A)
UNKNOWN: whether captions/tables/references must also be 12 pt
```

## 4d. PREP GUIDE (plain HTML artifact)

```yaml
url: https://claude.ai/artifact/AMpb8QkfwK4J3n4SqsSi3d   # 'Bottleneck Talk Prep', private
last_published: 1794808955-4270 (version 26, 2026-11-15)
local_copy: <scratchpad>/prep/bottleneck-prep.html (publish that path); if gone, Artifact read path index.html and strip the skeleton before <body> and the trailing </body></html>
views: Start here, Practice the talk (SLIDES array, one entry per slide in deck order, timer, default 15 min), Q&A (sl: = slide number, st:1 starred, f:1 'your call' tag, nos:1 not on slides), Demo, Reference
sync_rule: NOTES array = deck speaker notes per slide, re-extracted from the deck (split <aside> on <br>, html-unescape, nbsp -> space, strip); keep SLIDES order and sl: numbers in step with deck order
checks: bracket/string balance of the <script> block (no JS engine available); publishing needs a full Read of the live file first (Artifact read without path saves it; ~1253 lines, read in chunks)
demo_runbook: Mac + VM (CMDS: ssh tcpvm, sudo mn -c, modprobe, demo.py, livecap; stage cards with expected ping/queue readings; loss filter for stage 6)
```

## 5. CODE MAP (`/home/lucas/tcp-congestion`)

| path | role |
| --- | --- |
| topo/dumbbell.py, topo/shaping.py | Mininet dumbbell (router r1, bottleneck r1-eth1, netem on s2 receiver ports); htb + pfifo/red/fq_codel; RED min limit/6, max limit/2, p 0.1, no ecn flag |
| traffic/iperf.py, traffic/probes.py | iperf3 clients/servers; ping, ss, tc, tcpdump probes |
| run.py | YAML runner (`sudo python3 -u run.py <yaml> [--dry-run --only ID --trials N --staggered --udp-delay S --capture --resume DIR]`); `a+b` cca_mix alternates flows, first-named CCA gets h1 and the shortest mixed RTT |
| experiments/*.yaml | s1/s2/s3 main grids; follow-ups s1w, s1x, s1l, s3w, slong (section 2) |
| analysis/parse.py | results/<scenario> -> data/<scenario>_*.csv; newest copy wins per (config, trial); exits 1 if a scenario has no trials (writes nothing) |
| analysis/metrics.py | figures/<scenario>_summary.csv (mean + 95% CI); <first CCA>_share_pct for any 'a+b' mix (cubic/reno/bbr); --check |
| analysis/plots.py | F1-F8 for s1-s3 only (follow-ups have no plots) |
| demo.py | 6-stage live demo (CUBIC + BBR equal RTT, UDP 100%, fq_codel switch); per-second in-place block (rate bars, child-queue backlog x/167, hp->hr ping RTT); tcpdump of r1-eth1 to /tmp/demo.pcap (pre-created 644, ~40 MB/min); stage-6 LOSS_FILTER = dup_ack OR retransmission OR out_of_order; Ctrl+C-safe cleanup (F30); committed a859ed1; UNVERIFIED in the VM (parsing + redraw tested offline only) |
| devtools/gen_fake.py | fake results for pipeline tests (run in a scratch copy: it writes results/) |
| pyproject.toml, uv.lock | analysis deps for `uv run` |
| README.md | overview, follow-up table, WSL bring-up, demo + livecap, limitations; line ~72 wrongly says parse without results/ rewrites data/ (it exits 1, writes nothing) |
| helpers/mac.zsh, helpers/vm.sh | Mac and VM shell helpers (section 6) |
| report/ | main.tex, main.pdf, figs/ |
| data/, figures/ | tracked CSVs for all 8 scenarios (40 data files) |
| notebook.md, evidence/ | lab notebook (no follow-up entries) and step evidence |

## 6. SHORTCUTS

| name | where | usage |
| --- | --- | --- |
| analysis | WSL | `cd ~/tcp-congestion && uv run python -m analysis.parse <scen> && uv run python -m analysis.metrics <scen> --check` |
| tcp-push / tcp-pull | Mac | rsync code to / results back from tcpvm (original workflow) |
| cap, trial, shot | Mac | open trial-1 capture in Wireshark, newest trial folder, file screenshot into evidence/ |
| livecap | Mac | `ssh tcpvm 'tail -c +1 -f /tmp/demo.pcap' \| Wireshark -k -i -`; run after demo.py reaches stage 1 (earlier = stale or missing file) |
| rerun_flagged, lastblock, maxbacklog, udpq, probertt | VM | helpers/vm.sh |

## 7. FINDINGS (cause -> fix -> status)

| id | symptom | cause | fix | status |
| --- | --- | --- | --- | --- |
| F1 | switch-port bottleneck: UDP 48.7 Mbps, 0% loss | socket ownership kept across veth + OVS | bottleneck on router r1 | DONE |
| F2-F8 | ARP delay, idle-RTT noise, CLI silent, empty pcaps, zsh comments, word splitting, missing-config check | see git history of this file | fixed | DONE |
| F9 | goodput 47.8 Mbps at 50 Mbps | htb counts L2 bytes | utilization from wire bytes | DONE |
| F10-F14 | teardown in window, near-zero CI flags, stale re-parse, unpack error, plot gaps | analysis bugs | fixed | DONE |
| F15 | parallel S2 + S3 runs | cleanup() kills all iperf3 + mn -c | one scenario at a time | DONE (rule) |
| F16 | 11-packet buffer at 10 ms: Reno/CUBIC 23% util, BBR 97% | unpaced bursts, likely VM batching | reported as a result | DONE |
| F17/F18 | S2 TCP counted 5 s without UDP | UDP 0-60 s, TCP 0-65 s | overlap window 5-60 s | DONE |
| F19 | retrans_pct 2,365,104% | mean of per-flow ratios | bytes-weighted | DONE |
| F20 | notebook.md garbled passages | heredoc pastes into VM terminal (UNVERIFIED cause) | rebuilt on the Mac | DONE on Mac; VM copy UNVERIFIED |
| F21 | mixed-RTT CCA mixes always gave the first-named CCA the 20 ms path | flow_plan assigns CCAs and RTTs in the same order | s1x runs both orders; slide 8 labels the path order | DONE |
| F22 | 60 s competition shares still moving at the end (4x BDP CUBIC 72.6 -> 50.8 -> 50.8% by 20 s block) | deep queue / long path converges slowly | 180 s reruns (slong); report, slides, guide corrected; most other results steady after 25 s; minor drift left: S1 n4-mixed-bbr 20 ms flow 6.7% published vs ~5% settled | DONE |
| F23 | tectonic fails on WSL: fontspec cannot find TeX Gyre Termes | no Times New Roman or Termes system font | `cp /mnt/c/Windows/Fonts/times*.ttf <scratch>/fonts/`, fonts.conf including /etc/fonts/fonts.conf + `<dir><scratch>/fonts</dir>`, build with `FONTCONFIG_FILE=<scratch>/fonts.conf tectonic -o <scratch>/rep main.tex`, then copy main.pdf | DONE (recreate after WSL restart) |
| F24 | publish would overwrite user edits; editor re-saves slide files | Slides artifact keeps one live version | Artifact read every file you will publish, edit that copy | DONE (rule) |
| F25 | `git commit -m "..."` failed with a pathspec error | message contained double quotes | `git commit -F - <<'EOF'` | DONE |
| F26 | review 2026-11-15: 'BBR for delay at ~1x BDP if every sender runs BBR' (report Table III + conclusion, slide 14, guide Q&A) | evidence is single-flow (0.8 ms); S1 all-BBR pfifo measured 37-40 ms queue (CUBIC 32-34, Reno 25-29) and 3.6-10.6% retrans | report, slides 8/14/16, guide reworded 2026-11-15 | DONE |
| F28 | guide 'three numbers' card and takeaway: one CUBIC flow 494 ms -> '≈0 with fq_codel' | S3 single-flow runs were pfifo only; fq_codel was never run with one flow | replaced by measured 4 mixed flows 164 ms -> ≈10 ms (flows' RTT) | DONE |
| F29 | Wireshark at the router shows no dropped packets; resend may be labelled out-of-order, not fast retransmission | tcpdump on r1-eth1 sees packets after the qdisc, drops happen at enqueue | stage-6 filter `tcp.analysis.duplicate_ack \|\| tcp.analysis.retransmission \|\| tcp.analysis.out_of_order`; rehearse on real data | UNVERIFIED |
| F30 | Ctrl+C during node.cmd() skips demo cleanup (tcpdump, ping, iperf3, netns left) | Mininet sendCmd asserts `not self.waiting` | finally: waitOutput() on waiting nodes, then try stop probes / finally net.stop() | DONE (code), UNVERIFIED in VM |
| F27 | review 2026-11-15: 'fq_codel ~0 ms delay' | probe pair is a sparse flow that fq_codel serves first; bulk flows' iperf3 mean_rtt sits 2-15 ms above path RTT under fq_codel (includes startup) | clean number: TCP flows' per-second sender RTT 15-60 s minus path = 0.7-11.9 ms (series.csv); report/slides/guide say 'under 12 ms' for flows, '≈ 0' for a new flow | DONE |

## 8. STATE

| step | status | notes |
| --- | --- | --- |
| 1-8 environment, topology, validation, automation, S1-S3, analysis | DONE | main study frozen 2026-10-24 |
| follow-ups s1w, s1x, s1l, s3w, slong | DONE | 2026-11-15 on WSL; data and summaries committed |
| 9 report | DONE (UNVERIFIED whether submitted) | 8 pages; F26/F27 corrections committed f35ad61 |
| 10 presentation | IN_PROGRESS | deck v262 (16 slides) and prep guide v26 published; never rendered; upgraded demo committed a859ed1, never run; recording/transcript TODO |
| git | DONE | main == origin/main at a859ed1; only handoff.md uncommitted (user commits it as 'update handoff') |

## 9. OPEN_ITEMS (priority order)

1. TODO (user): step through deck version 262 in Present mode; check slides 3, 5, 6 (S2 sketch now drops every flow's packets), 7 (both animations must move: lines, grey total, red dots), 8 (3-number side card), 11 (dashed outline bar), 12, 13, 14 for overflow, overlap or wrapped titles. Fix by editing the slide file and republishing (4b).
2. TODO (user runs, Mac + VM): `# Mac: cd ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion && git pull && tcp-push && source helpers/mac.zsh`, then `# VM: cd ~/tcp-congestion && sudo mn -c && sudo python3 -u demo.py`, then at stage 1 `# Mac: livecap`. Build the Wireshark I/O graph once and save as profile 'demo' (tcp.dstport==5201, tcp.dstport==5202, udp.dstport==5204; bits; 100 ms). Expected: stage 2 ~48 Mbps, queue ~65-167/167, ping ~68 ms; 3 CUBIC falls toward ~5; 4 TCP ~0, ping ~73; 5 ~16 each, ping ~40. Check the stage-6 filter finds packets (F29) and the in-place redraw works in Terminal.app. Dry-run twice; paste output for R5 checks.
3. UNKNOWN (ask): talk length (prep timer default 15 min; deck now 16 slides), whether the report was already submitted, the deadline (2026-12-11 assumed), whether the deck must be in Google Slides (then GIFs replace the animations), whether captions/tables must be 12 pt.
4. TODO: copy the final report into evidence: `cp report/main.pdf evidence/step9-report/E9.1_report.pdf`, then commit.
5. TODO: rehearse twice with the prep guide, then E10.2 screen recording and E10.3 transcript (from speaker notes); set guide evidence rows E10.1-E10.3.
6. TODO (optional): back up WSL results/ (478 MB) somewhere outside WSL.
7. TODO: notebook entries for the follow-ups (R9); decide with the user which notebook copy is canonical now.
8. Optional gaps, only if the user asks: report figure fonts too small (F4 axis/legend ~5 pt; F6 legend over fq_codel bars; fix font sizes in analysis/plots.py, no page room for bigger figures); README line ~72 parse claim; bandwidth sweep (future work), a figure for follow-up results (no page room), RED/ECN variants, slide 8 / report BBR 20 ms flow 6.7% vs settled ~5%.
9. Old, low priority: VM commit/tag after 2026-10-24 fixes UNVERIFIED; guarded scp of the repaired notebook to the VM UNVERIFIED; reply 'future work' to the proposal parking-lot comment; free ~1.1 GB on the VM by deleting results/ (Mac copy complete); superseded report doc still has 7 old errors (ignore unless shared).

```bash
# WSL: code checks (syntax only; __pycache__ is root-owned so py_compile fails)
cd ~/tcp-congestion && python3 -c "import ast,glob; [ast.parse(open(f).read(),f) for f in glob.glob('topo/*.py')+glob.glob('traffic/*.py')+glob.glob('analysis/*.py')+['run.py','demo.py']]; print('ok')"
```

```bash
# WSL: data checks for every scenario, on a throwaway copy (metrics rewrites figures/)
rm -rf /tmp/tcpcheck && mkdir /tmp/tcpcheck && cd ~/tcp-congestion && cp -r run.py analysis experiments data figures topo /tmp/tcpcheck/ && cd /tmp/tcpcheck && for s in s1 s2 s3 s1w s1x s1l s3w slong; do uv run --project ~/tcp-congestion python -m analysis.metrics $s --check; done
```

```bash
# WSL: repo state
cd ~/tcp-congestion && git status -sb && git log --oneline -3
```

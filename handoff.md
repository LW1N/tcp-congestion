# handoff.md: agent handoff for CMPE 206 TCP congestion project

<!--
Format: optimized for AI agents. Facts are key: value lines or tables with exact identifiers.
Status values: DONE | TODO | IN_PROGRESS | UNVERIFIED | UNKNOWN. UNVERIFIED = implemented but never observed
working where it matters. UNKNOWN = ask the user or check before relying on it.
Last updated: 2026-11-17 (/handoff refresh: talk file is now 'TCP Congestion and Network Performance (RED v3 conclusions).pptx'
(slide 13 = questions recap, slide 14 = general recommendations); guide v48; git clean at 7912c94).
-->

## 0. READ_FIRST

1. Read this file, then `requirements.md` (course requirements: report sections, 6-8 pages, rubric 20/20/20/20/10/10).
2. Code and docs are edited on the user's Windows PC in WSL2 (`/home/lucas/tcp-congestion`); check `pwd`. The live demo runs on the Mac + VM (code reaches the VM via GitHub -> Mac `git pull` -> `tcp-push`). Claude cannot run sudo; the user runs experiments and demo.py and pastes output.
3. Deliverables: report `report/main.pdf` (8 pages, 4c), talk deck = a .pptx shown in Google Slides (4b, 16 slides), prep guide artifact (4d). All data is in git.
4. Deck edits: edit the user's latest .pptx in place with `devtools/pptx/` (never re-export the HTML deck: it would drop their notes and animations). The user edits the .pptx themselves between sessions: always ask which file is current and diff it first (4b edit_flow).
5. Highest priority: OPEN_ITEMS #2 (demo.py dry run with livecap on Mac + VM; never run), then #5 (rehearse, record). Talk file: 4b current_talk_file.
6. Prose rules: R12, R14 (user's voice). Slide rules: R13, R19, R20, R22, R23. Do not trust UNKNOWN items (OPEN_ITEMS 3a).

## 1. USER_RULES (must follow)

- R1: Every command complete and copy-pasteable. No placeholders, no "see above".
- R2: Label where each code block runs: `# WSL` (current), `# Mac`, `# VM`, `# mininet>`. Several commands meant to run in order each get their own block.
- R2a: Mininet CLI commands: one per block (Mininet forwards later pasted lines to stdin).
- R3: Prefer helper shortcuts (section 6) where they exist (Mac/VM only).
- R4: SUPERSEDED 2026-11-15: the WSL repo is the working copy, pushed to GitHub by the user.
- R5: When the user pastes terminal output, check it against expectations and look for anomalies.
- R6: Refer to the user with they/them.
- R7: After code changes run local checks (section 9) and a Sonnet subagent review of the diff (global CLAUDE.md). Fix real problems; reject wrong ones with a reason.
- R8: notebook.md: give entries as heredocs, never overwrite blindly; which copy (Mac/VM/WSL) is canonical is UNKNOWN (open item 7).
- R9: Notebook entries hold measured numbers, mechanisms, numbered Surprises, practical notes, Next.
- R10: The VM is shared; never assume it is up or clean (bring-up in section 3).
- R11: Use exactly the host form the user asks for (they once asked for `lucas@vm0.local` instead of `tcpvm`).
- R12: Deliverables must not read as AI-generated: varied sentence openings and lengths, no aphoristic 'Label: claim.' openers, some first person, exact numbers.
- R13: Slides: few on-slide words, visuals preferred, details in speaker notes, no H1-H5 labels or config ids on slides, define terms where first used, easy for an audience seeing it once.
- R14: Prose in the user's voice: reason-first openings, 'This ...' follow-ups, plain words, first person, no semicolons or em dashes.
- R15: Report: two-column IEEE, Times New Roman, 12 pt, 6-8 pages (keep at 8).
- R16: Do not start experiment runs; prepare files, dry-run them, give run commands. Long runs: wrap the whole loop in ONE `sudo bash -c '...'` (per-file sudo timed out and skipped s2r once).
- R17: The user commits with messages Claude drafts (no Co-Authored-By trailer), as `git commit -F - <<'EOF' ... EOF` (F25).
- R18: Hedge mechanisms that were not measured ("likely"); state cross-machine comparisons as such.
- R19: Never present an effect built into the setup as a finding (BDP-sized buffers make delay grow with RTT; RED/fq_codel low fill and ~5 ms delay are their targets). Say what is by design.
- R20: Slides and guide are checked for accuracy and for a once-only audience; after slide or guide changes run a Sonnet review of the change too.
- R21: A project review covers the published artifacts (talk .pptx, prep guide, proposal doc), not only the repo. report/main.tex is the only report source.
- R22: Prefer comparisons the audience can read across (queue x algorithm grids); when a comparison lacks data, propose a targeted run instead of mixing settings.
- R23: Anything in the .pptx must work in Google Slides: no embedded video (F39); GIFs, native entrance effects and fades work.
- R24: Preserve the user's own deck edits and note wording; match their notes format (plain lines, '-' bullets, header lines) when adding lines; save edits as a new file, never overwrite theirs.
- R25: Do not reword a pre-run prediction to fit results (integrity); the user accepted reframing slide 13 as questions instead (2026-11-17).

## 2. PROJECT

```yaml
user: Lucas Nguyen (solo)
course: CMPE 206, SJSU; option: TCP Congestion and Network Performance Analysis; tools: Mininet, iperf3, Wireshark
scenarios: {S1: competing TCP flows + single-flow baseline, S2: 3 TCP + 1 UDP, S3: buffer (router queue size) x delay}
dropped: [random-loss scenario, bandwidth sweep (fixed 50 Mbps), parking-lot topology (future work), path-length slide (tried 2026-11-17, user found it confusing)]
axes: {cca: [reno, cubic, bbr v1], qdisc: [pfifo, red, ared, fq_codel], buffer_x_bdp: [0.25, 1, 4], rtt_ms: [10..150]}
main_study (VM): {configs: 95, trials: 492, run: 2026-10-23..24}
follow_ups (WSL): {report counts 80 configs (51 S1, 17 S2, 12 S3) / 400 trials; slides-only s3q, s3qr, s3qrs add 82 trials (deck notes say 482 runs); 18 configs repeat VM settings, CIs overlap apart from small gaps (largest 10 ms / 5% loaded RTT at 4x BDP)}
red_decision: every RED number in report and slides comes from `ared` (5 ms target, F45); old `red` (S3, s3q) cited only as a check; `ared_slow` (F46) is a documented negative result
framing: loss-based (Reno, CUBIC) vs model-based (BBR v1) vs unresponsive (UDP)
headline: the router queue matters more than the CCA; fq_codel best or tied-best on delay and fairness everywhere
schedule: {submission: 2026-12-11 ASSUMED (UNKNOWN), report submitted: UNKNOWN}
```

Hypotheses (proposal, report Table II): H1 utilization at >=1x BDP: PARTLY (11-packet buffer at 10 ms: Reno/CUBIC 23%). H2 Reno favors short RTT more than CUBIC: SUPPORTED, BBR reverses it. H3 BBR wins shallow buffers, CUBIC recovers in deep: SUPPORTED on pfifo (even split once settled), not under RED. H4 line-rate UDP starves TCP, fq_codel fixes it: SUPPORTED, not by RED. H5 deep FIFO adds its drain time: CUBIC yes, Reno partly.

Key numbers (main study, pfifo unless noted): single flow util 99.98/99.97/97.5% (Reno/CUBIC/BBR), queue delay 22.6/27.9/0.8 ms; CUBIC vs BBR 1+1 10.6%, 2+2 1.9-3.3%, fq_codel 48.7-50.4%; 2-4 BBR flows 37-40 ms and 3.6-10.6% resent vs 2-4 CUBIC 32-34 ms and <0.06% (both near the ~40 ms 1x buffer; at 4x four BBR 64 ms vs four CUBIC 171 ms); S3 2+2 CUBIC 1.4/1.8/58.9% at 0.25/1/4x (51.1% settled); 4x single-flow delay CUBIC 34.5/162/494 ms; S2 pfifo TCP 35.5/23.1/10.7/0.05 Mbps, fq_codel ~35. fq_codel flows' own delay: Reno/CUBIC <4 ms, BBR up to 35 ms (F32). Mixed RTT 20 vs 80 ms, 20 ms flow's share (2 flows): pfifo Reno 61 / CUBIC 51 / BBR 25%, RED 79/76/54, fq_codel 58/53/51.

| follow-up | result |
| --- | --- |
| s1w, s1x, s1l, s3w, slong | Reno pairs (Reno vs BBR 10.0% pfifo, 43.8% fq_codel), swapped paths (CUBIC on 80 ms vs BBR on 20 ms 46.8%), Reno vs CUBIC 180 s 38.0%, 2 Reno + 2 BBR 1.9/2.3%, 180 s reruns (4x CUBIC 51.1%, Reno 48.1%) |
| s3q | 4 flows, 4x BDP (834 pkts, 200 ms), 50 ms, 180 s. Fill % pfifo/red/fq_codel: Reno 78/12/0.9, CUBIC 85/15/0.9, BBR 30/26/6.7, mix 75/23/6.7 |
| s1r (ared) | CUBIC 5.2%, Reno 4.9% vs one BBR (pfifo same machine 10.9/10.0); BBR 20 ms vs CUBIC 80 ms: CUBIC 2.2% (pfifo 46.8); Reno util 83-87%, CUBIC 94-97%; mixed-RTT Jain Reno 0.75/0.73, CUBIC 0.78/0.79 (1/RTT model 0.74/0.77); loss-based delay 0.1-0.9 ms |
| s2r (ared) | TCP 34.0/22.4/10.9/2.1 Mbps (CUBIC) at UDP 25-100%: RED does not fix starvation |
| s3r (ared) | 2+2 CUBIC 2.4/2.5/2.4% at 0.25/1/4x, probe delay 4.6/4.4/4.8 ms (its target) |
| s3qr (ared) | fill 0.3/0.4/2.7/2.3% (by design: 5 ms ~ 21 pkts ~ 2.5%); Reno util 86% (fq_codel 95%, same machine) |
| s1rs, s2rs, s3qrs (ared_slow) | negative result (F46): lockouts after slow start, Reno 63-82% in the last 30 s; s3qrs Reno no data |

## 3. ENVIRONMENT

```yaml
wsl_pc (current):
  host: Windows PC, AMD Ryzen 5 5600X, 15 GB RAM; Ubuntu 26.04.1 in WSL2, kernel 6.18.58.1-microsoft-standard-WSL2, systemd on
  repo: /home/lucas/tcp-congestion (origin https://github.com/LW1N/tcp-congestion, PUBLIC)
  apt: {mininet: 2.3.0-1.1build1, openvswitch-switch: 3.7.1-2, iperf3: 3.20-2, tcpdump: 4.99.6-1, iproute2: 6.19.0, tmux}
  python: system 3.14.4 (runner under sudo); analysis via uv 0.13.7 (~/.local/bin/uv)
  latex: tectonic 0.17.0 (~/.local/bin); needs Times New Roman via fontconfig (F23)
  modules: not loaded at boot; after every WSL restart run bring_up_wsl
  raw_results: results/ 2.2 GB (follow-ups only), gitignored, only on this PC (no backup)
  limits: sudo needs the user's password; no node, no browser, no LibreOffice/poppler: slides checked only with devtools/pptx/render.py (rough), PDFs with pypdf text extraction
  scratchpad: per session, wiped on WSL restart; keep reusable scripts in devtools/
  uv_recipes: pptx skill scripts need `--python 3.12 --with lxml --with defusedxml --with python-pptx`; pdf text `--no-project --with pypdf==5.4.0 python -I`; deck tools `--no-project --with lxml [--with pillow==11.3.0]`
bring_up_wsl: "# WSL: sudo modprobe -a tcp_bbr sch_htb sch_red sch_fq_codel sch_netem openvswitch && sudo systemctl enable --now openvswitch-switch && cat /proc/sys/net/ipv4/tcp_available_congestion_control   (expect reno cubic bbr)"
mac (demo machine): Apple M2, zsh, repo ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion (git pull); results/ 2.6 GB of the main study (46 pcaps); Wireshark /Applications/Wireshark.app/Contents/MacOS/Wireshark (UNVERIFIED)
vm (demo host): UTM, Ubuntu 26.04.1 ARM64, kernel 7.0.0-38-generic, 4 vCPU, 3.3 GiB; host vm0, user lucas, alias tcpvm; ~/tcp-congestion; ~1.4 GB free
vm_bring_up: ["# Mac: ssh tcpvm 'echo connected to $(hostname)'", "# VM: cd ~/tcp-congestion && sudo -v && sudo mn -c"]
```

## 4. DOCS (Claude Docs on claude.ai)

| key | url | project_id | body_node_id | last_known_rev | status |
| --- | --- | --- | --- | --- | --- |
| proposal | https://claude.ai/artifact/MHnQC8nYRexNPwSauG9wwK | a44ea6f5-2c85-42dd-80ed-b60386cd4e56 | a6564636-68fa | 65 (2026-11-17) | submitted; historical; open parking-lot comment 9229d96b-b330 |

Deleted 2026-11-17 at the user's request: report doc (7vJiBvAn1QoxLYNaCXatnG) and implementation guide doc (BokvUU7o8zuiJZKsWbbiRN). Doc tools: load the docs skill, `guide(items=["topic.index"])`, read deltas with `{"kind":"view","sinceRev":<rev>}`.

## 4b. SLIDE DECK (.pptx in Google Slides)

```yaml
current_talk_file: /mnt/c/Users/lucas/Downloads/TCP Congestion and Network Performance (RED v3 conclusions).pptx   # 16 slides, 2026-11-17; = the user's '(RED v3 questions)(1).pptx' (their slide 13 answer edits + slide 14 notes restructure) + slide 14 generalized by devtools/pptx/conclusions_slide.py (title 'What to deploy at a shared bottleneck', scope line 'Recommendations from one emulated 50 Mbps link (BBRv1, no ECN): directions, not guarantees', FIFO branch 'Size it near 1× BDP' with too small / about 1× / too large principles, closing line on FIFO/RED queues, BBR* footnote removed; wording narrowed after a Sonnet review) + slide 13 row 1 'FIFO: BBR, mostly · fq_codel: even split'. The user may have edited it since: ask
derived_from: '(RED v3 questions)(1).pptx' (the user's latest download, still in Downloads); older versions (v3, v4, v5 path-length tries) were deleted by the user
edit_flow: copy the user's latest file to a scratch folder; unzip to un/; edit with devtools/pptx (helpers in edit_deck.py; ids come from shapes.py/timing.py because Google renumbers shape ids on every download); pack.py <orig> out.pptx; pptx skill validate.py out.pptx --original <orig>; render.py the changed slides; slide_text.py diff vs the original must show only intended lines; save as a NEW file in Downloads (R24)
adding_slides: pptx skill add_slide.py leaves the new slide without notes: copy a notesSlide part + rel + content-type override; renumber footers 'n / N', eyebrows 'NN ·' (= n-1) and progress bars (fill A78BFA at y 1040, width 1664*n/N px)
slides: 1 cover, 2 problem, 3 topology, 4 CCAs, 5 queues, 6 scenarios, 7 families, 8 S1 (RED bars; delay card with resend %), 9 S2 (RED bars), 10 capture, 11 S3 share, 12 buffer fill (RED · 5 ms target), 13 'What the experiments answered' (4 questions in talk order; notes point to report Table II for the predictions), 14 'What to deploy at a shared bottleneck' (general principles, scope line), 15 close, 16 demo
click_steps: 3:6, 4:1, 5:0, 6:4, 7:3, 8:5, 9:5, 10:3, 11:4, 12:3, 13:5, 14:3, 16:7
user_edits_in_v3: slide 6 S3 card 'Queue Size' (RTT chip removed), strip 'Reno, CUBIC, BBR on pfifo, fq_codel, and RED'; slide 8 stars removed, delay card '(4–11% of data resent)', '32-34 ms', '(<0.1% resent)', Reno vs CUBIC card text removed; notes restructured as plain bulleted lines
known_issue: still present 2026-11-17 in the conclusions file: slide 8 click 5 shows the empty box (shape 194) left from the Reno vs CUBIC card, and the CUBIC lines (shapes 257, 252; y 674-803) run past the delay card (243, ends y 766); flagged to the user, unchanged
style: bg #111019, card #1C1B27, text #F4F3F7, muted #A9A7BB, footer #8A889C; pfifo #FFB23E, RED #A78BFA, fq_codel #4FD1E0, drop #FF6B6B; fonts Schibsted Grotesk + IBM Plex Mono; 1920x1080 px frame = 6350 EMU/px
animations: looping GIFs on slides 1-7 (from the 2026-11-16 build), native entrance effects, fades
html_deck_artifact: https://claude.ai/artifact/2GZMMEVvtSyVmNHZ44rzys  STALE (no RED, no user note edits); do not export from it
```

## 4c. FINAL REPORT (LaTeX)

```yaml
source: report/main.tex   # IEEEtran conference 12pt letter; fontspec Times New Roman, fallback TeX Gyre Termes
output: report/main.pdf   # 8 pages, committed 1d73cc0; evidence/step9-report/E9.1_report.pdf is identical
build_wsl: F23, then the page count (section 9) must print 8; float order: Table III and Fig. 7 are defined right after Fig. 6 on purpose
page_budget: zero; one added word flipped it to 9 pages on 2026-11-17; any addition needs a trim
red_content: Adaptive RED [ared bib] 5 ms target; S1/S2/S3 RED results; H1 model 79-86% vs 83-87%; H2 1/RTT model 0.74 vs 0.75; Table III row 'RED instead of fq_codel'; conclusion '892 trials on two machines', 'several BBR flows kept a 1× BDP FIFO about as full as CUBIC did'
removed_to_fit: Testbed Lessons subsection, condensed Scenarios paragraph, Table III footnote, several side sentences
not_in_report: s3q/s3qr buffer-fill grids, path-length shares, negative queue-delay explanation
UNKNOWN: whether captions/tables/references must also be 12 pt
```

## 4d. PREP GUIDE (plain HTML artifact)

```yaml
url: https://claude.ai/artifact/AMpb8QkfwK4J3n4SqsSi3d   # 'Bottleneck Talk Prep', private
last_published: version 48 (2026-11-17): NOTES and slides 13/14 synced to the conclusions deck; before: v47 16 slides, slide 13 = 4 questions, utilization metric -> slide 14, 11-packet Q&A sl:14
edit_flow: Artifact read (no path) saves the page; Read every line; strip up to and including '<body>\n' and the trailing '</body></html>'; edit; publish to the url (small changes: `edits` on publish)
data_arrays: grep '^var NOTES=', '^var SLIDES=', '^var QA=', 'var STEPS=', 'var RUBRIC=', 'var METRICS=', 'var MEAS=', 'var GL=', 'var CMDS=', 'var STAGES='
sync_rule: NOTES = deck notes per slide (paragraphs and <a:br> lines, nbsp -> space, strip); SLIDES order, clicks and Q&A sl: numbers follow the deck
checks: string/bracket balance of the <script> block plus regex ',\s*,' and '\[\s*,' (F38)
```

## 5. CODE MAP (`/home/lucas/tcp-congestion`)

| path | role |
| --- | --- |
| topo/dumbbell.py, topo/shaping.py | Mininet dumbbell (router r1, bottleneck r1-eth1, netem on s2 ports); htb + pfifo / red (min limit/6, max limit/2) / ared (min 2.5 ms = 15625 B at 50 Mbps, max 3x, burst 19 -> tc ewma 4, `adaptive`) / ared_slow (burst 201 -> ewma 12) / fq_codel |
| traffic/iperf.py, traffic/probes.py | iperf3 clients/servers; ping, ss, tc, tcpdump probes |
| run.py | YAML runner (`sudo python3 -u run.py <yaml> [--dry-run --only ID --trials N --staggered --udp-delay S --capture --resume DIR]`); records the git commit per trial |
| experiments/*.yaml | 16 files: s1/s2/s3 + follow-ups s1w s1x s1l s3w slong s3q s1r s2r s3r s3qr s1rs s2rs s3qrs; write `qdisc` in every grid entry |
| analysis/parse.py, metrics.py | results -> data/<scen>_*.csv -> figures/<scen>_summary.csv (mean + 95% CI), `--check` |
| analysis/plots.py | F1-F8; F2/F4/F6 add ared rows from s1r/s2r/s3r via red_only(), legend 'RED*' |
| demo.py | 6-stage live demo; tcpdump of r1-eth1 to /tmp/demo.pcap; terminal side DONE in the VM 2026-11-17 (run 1); livecap/Wireshark side UNVERIFIED |
| devtools/verify_red.py | independent raw-file check of the RED runs (`python3 devtools/verify_red.py rows.json`) |
| devtools/pptx/ | in-place .pptx tools (README there): edit_deck.py, apply_red.py, questions_slide.py, conclusions_slide.py, pack.py, shapes.py, timing.py, notes_lines.py, render.py, edit_guide.py |
| README.md, report/, data/, figures/, evidence/, notebook.md | overview + follow-up table + limitations ('Three RED settings'); report; tracked CSVs for 16 scenarios; evidence; notebook (no follow-up entries yet) |

## 6. SHORTCUTS

| name | where | usage |
| --- | --- | --- |
| analysis | WSL | `cd ~/tcp-congestion && uv run python -m analysis.parse <scen> && uv run python -m analysis.metrics <scen> --check` |
| tcp-push / tcp-pull | Mac | rsync code to / results back from tcpvm |
| cap, trial, shot | Mac | open trial-1 capture in Wireshark, newest trial folder, file screenshot into evidence/ |
| livecap | Mac | `ssh tcpvm 'tail -c +1 -f /tmp/demo.pcap' \| Wireshark -k -i -`; run after demo.py reaches stage 1 |
| rerun_flagged, lastblock, maxbacklog, udpq, probertt | VM | helpers/vm.sh |

## 7. FINDINGS (cause -> fix -> status)

| id | symptom | cause | fix | status |
| --- | --- | --- | --- | --- |
| F1 | switch-port bottleneck: UDP 48.7 Mbps, 0% loss | socket ownership kept across veth + OVS | bottleneck on router r1 | DONE |
| F2-F8, F10-F14, F17-F19 | early pipeline and analysis bugs | see git history | fixed | DONE |
| F9 | goodput 47.8 Mbps at 50 Mbps | htb counts L2 bytes | utilization from wire bytes | DONE |
| F15 | parallel runs | cleanup() kills all iperf3 + mn -c | one scenario at a time | DONE (rule) |
| F16 | 11-packet buffer at 10 ms: Reno/CUBIC 23%, BBR 97% | unpaced bursts, likely VM batching | reported with caveat; off slide 13 (Q&A only) | DONE |
| F20 | notebook.md garbled | heredoc pastes into VM terminal (UNVERIFIED) | rebuilt on the Mac | DONE on Mac; VM copy UNVERIFIED |
| F21 | mixed-RTT mixes gave the first-named CCA the 20 ms path | flow_plan order | s1x runs both orders | DONE |
| F22 | 60 s shares still moving at 4x | deep queue converges slowly | 180 s reruns (slong) | DONE |
| F23 | tectonic fails on WSL | no Times New Roman | `cp /mnt/c/Windows/Fonts/times*.ttf <scratch>/fonts/`; fonts.conf `<include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir><scratch>/fonts</dir>`; `cd report && FONTCONFIG_FILE=<scratch>/fonts.conf tectonic -o <scratch>/rep main.tex`; copy main.pdf | DONE (recreate per session) |
| F24, F37 | publish overwrote / refused | artifact keeps one live version; a `paths` read does not count as viewing | read before publishing; bare Artifact read first | DONE (rule) |
| F25 | `git commit -m "..."` pathspec error | double quotes | `git commit -F - <<'EOF'` | DONE |
| F26 | 'BBR for delay if every sender runs BBR' | single-flow evidence only | reworded everywhere | DONE |
| F27/F32 | fq_codel delay overstated as low for all flows | median over all CCAs | Reno/CUBIC <4 ms, BBR up to 35 ms in its own queue | DONE |
| F28, F31, F33-F35 | stale or by-design claims in deck/guide | text drift, BDP construction, VM ping wake-up | fixed | DONE |
| F29 | Wireshark at the router shows no drops | capture is after the qdisc | stage-6 filter dup_ack OR retransmission OR out_of_order | UNVERIFIED |
| F30 | Ctrl+C during node.cmd() skipped demo cleanup | Mininet sendCmd assert | waitOutput(), stop probes, net.stop() | DONE (code), UNVERIFIED in VM |
| F36 | small leftovers | - | dead code removed 2026-11-17; left: report 'both fell to 23%' (22.8/23.6), slide 7 eyebrow 'Background' in the experiments section | TODO (optional) |
| F38 | guide got `},,` | replacement kept a comma | regex check before publishing | DONE (rule) |
| F39 | video in .pptx shows a still in Google Slides | Google Slides never plays embedded video | looping GIFs | DONE |
| F40, F41 | slide 14 elbow arrows; media GUID | exporter routing; GUID from memory | native lines; correct GUID | DONE |
| F42 | Table III RED rows had no RED data | S1/S2 lacked RED | s1r + s2r run, rows now evidenced | DONE |
| F43, F45 | `red` delay restated its buffer-scaled thresholds | thresholds = limit/6, limit/2 | `ared` with fq_codel's 5 ms target for all RED follow-ups | DONE |
| F44 | notebook says RED 4x '368 drops'; data shows 10,641-11,844 | UNKNOWN | correct with open item 7 | TODO |
| F46 | ared's Reno util cost and RTT bias might be the fast average (tc ewma 1/16) | tested with ared_slow (ARED paper's w_q) | slow average locked flows out and was worse, so the ared results stand; report says so in one sentence | DONE |
| F47 | per-file `sudo` in a long loop skipped s2r (`sudo: timed out`) | sudo timestamp expired between files | one `sudo bash -c` for the whole loop (R16) | DONE (rule) |
| F48 | pack.py dropped a newly added slide | it copied only the original's members | pack.py now adds new parts | DONE |

## 8. STATE

| step | status | notes |
| --- | --- | --- |
| 1-8 environment, topology, validation, automation, S1-S3, analysis | DONE | main study frozen 2026-10-24 |
| follow-ups incl. RED (s1r s2r s3r s3qr) and ared_slow (s1rs s2rs s3qrs) | DONE | run 2026-11-16/17, verified from raw files (devtools/verify_red.py), data committed |
| 9 report | DONE (UNKNOWN whether submitted) | 8 pages with RED; committed 1d73cc0 |
| 10 presentation | IN_PROGRESS | deck = 4b current_talk_file; guide v48; demo never run; rehearsal, recording, transcript TODO |
| review 2026-11-17 | DONE | code, all 16 experiment dry-runs, metrics --check (13 OK, s1rs/s3qrs fail by design), figures regenerate identically, report refs/cites, docs |
| git | DONE | main at 7912c94 = origin/main (2026-11-17); clean except this handoff.md |

## 9. OPEN_ITEMS (priority order)

1. DONE 2026-11-17: RED results in the deck; slide 13 reframed as 'What the experiments answered' (4 questions); slide 14 rewritten as general recommendations with a scope line; talk file = 4b current_talk_file. Optional: fix slide 8's empty click-5 box (4b known_issue) if the user wants; the user may add a note line for slide 14's new closing line (no note covers it yet).
1i. Q&A prep answered in chat 2026-11-17, not yet in the guide: ECN (marks instead of drops; senders never negotiated it, tcp_ecn=2, RED had no `ecn` flag; would likely help Reno/CUBIC under RED, not BBRv1 or UDP; the guide's 'Was ECN on?' Q&A covers most of it) and why two switches (s1 merges senders onto one router port = one shared queue; s2 holds per-receiver netem delay after the bottleneck so flows get different RTTs without a second queue; r1 is the bottleneck because shaping a switch port never dropped, F1). Optional: add the switches answer to the guide's 'Why a dumbbell topology?' Q&A if the user wants.
1a. DONE: animation build scripts lost; superseded by devtools/pptx.
1b. REMOVED: the HTML deck artifact is no longer used (4b html_deck_artifact).
1c, 1d, 1f, 1g, 1h, 1g2, 1h2: DONE 2026-11-17 (RED runs, verification, docs update, project review, multi-BBR delay scoping); details in sections 2, 4c, 7.
1e. UNKNOWN (user never decided): extra AQM single-flow runs (s3a: n1 x rtt 10/50/150 x reno/cubic/bbr x fq_codel/ared at 1x BDP, ~2.1 h) to back Table III 'fq_codel, any CCA'. Ask once if time allows; otherwise drop.
2. IN_PROGRESS (run 1 2026-11-17, terminal output matched: s2 48.3 Mbps, queue 89, ping 61; s3 CUBIC 6.3 / BBR 41.9, ping 70; s4 TCP 0, UDP 48.3, queue 166, ping 73; s5 14.7/14.7/16.9, total 46.3, queue 125 (UDP's own subqueue, fq_codel drops from the fattest flow), ping 40; htb direct_packets_stat 5 = packets during the qdisc swap. Still UNVERIFIED: livecap, I/O graph, stage-6 filter, clean exit, second run. tcp-push prints Permission denied on root-owned __pycache__ on the VM: harmless; fix = --exclude __pycache__ in helpers/mac.zsh, not done) (user runs, Mac + VM): `# Mac: cd ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion && git pull && tcp-push && source helpers/mac.zsh`, then `# VM: cd ~/tcp-congestion && sudo mn -c && sudo python3 -u demo.py`, then at stage 1 `# Mac: livecap`. Build the Wireshark I/O graph once, save as profile 'demo' (tcp.dstport==5201, tcp.dstport==5202, udp.dstport==5204; bits; 100 ms). Expected: stage 2 ~48 Mbps, queue ~65-167/167, ping ~68 ms; 3 CUBIC falls toward ~5; 4 TCP ~0, ping ~73; 5 ~16 each, ping ~40. Check the stage-6 filter (F29) and the in-place redraw in Terminal.app. Dry-run twice; paste output (R5).
3. DONE 2026-11-16: F32-F35, s3q.
3a. UNKNOWN (ask): talk length (prep timer default 15 min, 16 slides), whether the report was submitted, the deadline (2026-12-11 assumed), whether captions/tables must be 12 pt.
4. DONE 2026-11-17: evidence/step9-report/E9.1_report.pdf = report/main.pdf (re-copy after any report rebuild).
5. TODO: rehearse twice with the prep guide (Practice tab), then E10.2 screen recording and E10.3 transcript (from speaker notes); set guide evidence rows E10.1-E10.3.
6. TODO (optional): back up WSL results/ (2.2 GB) outside WSL.
7. TODO: notebook entries for the follow-ups incl. s3q, RED and ared_slow (R9) plus the F44 correction; decide with the user which notebook copy is canonical.
8. Optional, only if the user asks: F36 leftovers; report figure fonts small (F4 legend, F6 legend over fq_codel bars); future work (bandwidth sweep, ECN, parking lot).
9. Old, low priority: VM commit/tag after 2026-10-24 fixes UNVERIFIED; repaired notebook not copied to the VM; reply 'future work' to the proposal parking-lot comment; free ~1.1 GB on the VM.

```bash
# WSL: code checks (syntax only; __pycache__ may be root-owned so py_compile fails)
cd ~/tcp-congestion && python3 -c "import ast,glob; [ast.parse(open(f).read(),f) for f in glob.glob('topo/*.py')+glob.glob('traffic/*.py')+glob.glob('analysis/*.py')+glob.glob('devtools/*.py')+glob.glob('devtools/pptx/*.py')+['run.py','demo.py']]; print('ok')"
```

```bash
# WSL: data checks on a throwaway copy (metrics rewrites figures/); expect 'all configurations OK' 13 times
rm -rf /tmp/tcpcheck && mkdir /tmp/tcpcheck && cd ~/tcp-congestion && cp -r run.py analysis experiments data figures topo /tmp/tcpcheck/ && cd /tmp/tcpcheck && for s in s1 s2 s3 s1w s1x s1l s3w slong s3q s1r s2r s3r s3qr; do uv run --project ~/tcp-congestion python -m analysis.metrics $s --check; done
```

s1 also prints a late-BBR convergence table (expected). s1rs/s2rs/s3qrs are left out: ared_slow lockouts fail the CI check by design. Never commit regenerated figures/s{1,2,3}_summary.csv (float digits differ from the VM-generated ones).

```bash
# WSL: report page count without a PDF library (expect 8)
cd ~/tcp-congestion && python3 -c "import re,zlib; b=open('report/main.pdf','rb').read(); n=len(re.findall(rb'/Type\s*/Page\b(?!s)',b))
for m in re.finditer(rb'stream\r?\n',b):
    try: n+=len(re.findall(rb'/Type\s*/Page\b(?!s)',zlib.decompress(b[m.end():b.find(b'endstream',m.end())])))
    except Exception: pass
print(n)"
```

```bash
# WSL: repo state
cd ~/tcp-congestion && git status -sb && git log --oneline -3
```

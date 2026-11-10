# handoff.md: agent handoff for CMPE 206 TCP congestion project

<!--
Format: optimized for AI agents. Facts are key: value lines or tables with exact identifiers.
Status values: DONE | TODO | IN_PROGRESS | UNVERIFIED | UNKNOWN. "UNVERIFIED" = implemented but never
observed working where it matters. "UNKNOWN" = ask the user or check before relying on it.
Last updated: 2026-11-09, night (final report rebuilt as IEEE two-column LaTeX in tcp-congestion/report/, 12pt Times New Roman, in the user's own voice; Sonnet review fixes applied; committed and pushed as 9148bbd; Claude Doc report superseded). Earlier 2026-11-09: deck restyled to Capture Dark + animations (v25); handoff.md/requirements.md moved into tcp-congestion/; re-review of report + deck (OPEN_ITEMS #0). 2026-10-24: deck built; report rewritten for style; F18/F19 fixed; notebook repaired. Update STATE and OPEN_ITEMS when anything changes.
-->

## 0. READ_FIRST

1. Read this file fully before acting. It lives at `tcp-congestion/handoff.md` (moved from the project root 2026-11-09; a session started in `project/` must open it explicitly). Then read `requirements.md` (same folder) (course requirements; the report must satisfy its "Final Report" and "Evaluation Criteria" sections).
2. Doc state may have changed since this file was written. Before editing a doc, read its changes since the last known revision (section 4): `read(ref node <body_node_id>, payload {"kind":"view","sinceRev":<rev>})`.
3. Do not trust STATUS=UNKNOWN items. Ask the user or check (section 9).
4. All experiments are finished and the data is frozen (tag s3-done). Step 9 report: the deliverable is now `report/main.tex` -> `report/main.pdf` (IEEE two-column, section 4c); the user said 'It looks good' on 2026-11-09. The Claude Doc report (section 4) is superseded and still holds 7 errors fixed only in main.tex. Step 10: slide deck DONE as a draft (section 4b); rehearsals, recording and transcript remain.
5. Highest-priority open items: OPEN_ITEMS #4a (copy report/main.pdf over evidence/step9-report/E9.1_report.pdf; ask whether captions/tables/refs must also be 12 pt) and #5a - the user should step through the restyled deck (v25) in Present mode (none of the 4 live animations or the click builds have been seen rendered), then rehearse with demo.py. Also still unconfirmed: #1 (VM commit after the report fixes) and #1b (guarded scp of the repaired notebook.md to the VM).
6. Before editing the deck, read section 4b (file layout, publish/conflict rules, x-embed constraints) and the memory files writing-not-ai-sounding.md and slides-visual-first.md. Before writing any prose (report, notes, transcript), read memory user-writing-voice.md (R14).

## 1. USER_RULES (must follow)

- R1: Every command is complete and copy-pasteable. No placeholders, no paths/IDs for the user to assemble, no "see above".
- R2: Label each code block's first line with where it runs: `# Mac` | `# VM` | `# VM, inside tmux s1` | `# VM, outside tmux` | `# mininet>`.
- R2a: Mininet commands: ONE command per code block, label as a trailing comment (`h1 ping -c 20 h5   # mininet>`). While a foreground command runs, Mininet forwards further pasted lines to its stdin. Bash blocks may hold several one-line commands (no backslash continuations).
- R3: Prefer helper shortcuts (section 6) over raw paths in instructions.
- R4: Code lives as real files in `tcp-congestion/` on the Mac; the user pushes with `tcp-push`. Never paste whole programs into a doc.
- R5: When the user pastes terminal output or says "verify", check it against the current step's "Done when" criteria and look for anomalies (several real bugs were found this way: F9-F14).
- R6: Refer to the user with they/them.
- R7: After any code change: run local checks (section 9), tell the user to `tcp-push`, and update the guide doc if commands, file names, interfaces, or addresses changed.
- R8: notebook.md canonical copy is on the VM (~/tcp-congestion/notebook.md). Default: give notebook entries as a `cat >> notebook.md <<'EOF'` heredoc for the VM; never overwrite it blindly. Exception the user asked for on 2026-10-24: repair the Mac mirror (tcp-congestion/notebook.md) and have the user copy it with a guarded scp that only overwrites if the VM copy's md5 still equals the last pulled copy. tcp-push does NOT carry notebook.md; tcp-pull overwrites the Mac copy. Screenshot links in notebook entries only if the files reach the VM via tcp-push (they do not: evidence/ is not pushed).
- R9: The user often asks for a "notebook entry" after each step; it should hold measured numbers, mechanisms ("why"), surprises (numbered Surprise N), practical notes, and Next.
- R11: When the user asks for a specific host form in a command (on 2026-10-24 they asked for `lucas@vm0.local` instead of `tcpvm` in the ssh/scp notebook command), use it exactly. Why they preferred it is UNKNOWN; `tcpvm` is the configured alias and resolves to lucas@vm0.local.
- R12: Written deliverables (report, slides, speaker notes, transcript) must not read as AI-generated: vary sentence openings and lengths, no aphoristic 'Label: claim.' openers or chiasmus, some first person ('I measured'), captions in varied shapes. Keep every number exact.
- R13: Slides: very few on-slide words (target <= ~25 per slide), prefer images, graphs, diagrams and animations; detail goes in speaker notes (<aside>). Every slide must make sense to someone who has not read the proposal or report: no H1-H5 labels, no config ids, define terms (CCA, RTT, BDP, Jain's index) where first used.
- R14: Prose deliverables use the user's own voice: sample = paragraphs 4-5 (page 2) of project/CMPE 272 Group Reflection.pdf (paragraphs 1-3 are teammates'). Reason-first openings, 'This ...' follow-ups, plain words, first person, no semicolons or em dashes in prose. Details in ~/.claude/projects/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/memory/user-writing-voice.md (memory dir of sessions started in project/, not tcp-congestion/).
- R15: Report format (user, 2026-11-09): two-column IEEE style, Times New Roman, 12 pt, 6-8 pages.
- R10: The VM is shared with the user's other work and is brought up and down as needed. Never assume it is running or clean; any VM instruction set starts from the bring-up block (section 3 vm_lifecycle).

## 2. PROJECT

```yaml
user: Lucas Nguyen (solo; no team)
course: CMPE 206, SJSU
option: TCP Congestion and Network Performance Analysis
required_tools: [Mininet, iperf3, Wireshark]
requirements_file: ./requirements.md
scenarios:              # 3 = minimum allowed by requirements
  S1: competing TCP flows, single-flow baseline folded in   # tests H1, H2, H3
  S2: 3 TCP + 1 UDP on one bottleneck                       # tests H4
  S3: buffer size x propagation delay                       # tests H1, H3, H5
dropped: [random loss scenario, bandwidth sweep, parking-lot extension]   # parking lot = future work in report
comparison_axes: {cca: [reno, cubic, bbr], qdisc: [pfifo, red, fq_codel], buffer_x_bdp: [0.25, 1, 4]}
configs: {S1: 35, S2: 24, S3: 36, total: 95}
trials_analyzed: {S1: 175 + 3 staggered, S2: 129 + 2 late-UDP, S3: 183, total: 492}
trial_time_s: 75        # measured
schedule: {data_freeze: done 2026-10-24 (tag s3-done), submission: 2026-12-11 ASSUMED}
hypotheses_and_verdicts:
  H1: {claim: ">90% util at >=1x BDP; 0.25x BDP Reno ~85-90%, CUBIC near full, BBR unaffected", verdict: PARTLY (10 ms / 11-pkt buffer collapse to 23% unpredicted)}
  H2: {claim: "same CCA+RTT Jain >0.95; mixed RTT favors short RTT more under Reno than CUBIC", verdict: SUPPORTED (+ BBR reverses bias: long RTT wins)}
  H3: {claim: "BBR beats CUBIC in shallow buffers; CUBIC recovers in deep", verdict: SUPPORTED on pfifo (RED keeps BBR dominant)}
  H4: {claim: "UDP >=100% starves TCP; fq_codel restores fairness", verdict: SUPPORTED (TCP < 0.1 Mbps beside 100% UDP after F18; cost: UDP jitter 0.6-0.8 ms at 75-100% load)}
  H5: {claim: "deep pfifo adds ~drain time under loss-based; fq_codel/BBR low", verdict: SUPPORTED for CUBIC (80-86% of drain), PARTLY for Reno (64-71% at 10/50 ms = 2.5-5 BDP cycle model 69%; 41% at 150 ms, cannot regrow in 60 s)}
headline: queue discipline matters more than CCA; fq_codel best or tied-best in every tested condition
```

Key numbers (5-trial means, CI mostly <1%): n1 util Reno/CUBIC 99.98%, BBR 97.5%; n1 queue delay CUBIC 27.9, Reno 22.6, BBR 0.8 ms; CUBIC share vs BBR pfifo 10.6% (S1 n2), 1.4/1.8/58.9% at 0.25/1/4x (S3 n4), fq_codel 48-50%; S2 (after F18, window 5-60 s) pfifo TCP 35.5/23.1/10.7/0.05 Mbps at UDP 25/50/75/100% (model: (50 - 1.035 x UDP payload rate) x 1448/1514 = 35.4/23.1/10.7/0), fq_codel 35.1-35.4 (Reno 33.2-33.9), UDP loss at 100% pfifo 3.6%; staggered S1: CUBIC ~5.1 Mbps after BBR joins, BBR ~42; H1 model: 0.25x BDP predicts Reno 89% (meas 86.7), CUBIC 98% (98.2); S3 4x BDP CUBIC queue delay 34.5/162/494 ms at RTT 10/50/150; 4-flow 4x BDP pfifo 164, RED 48, fq_codel ~0 ms.

## 3. ENVIRONMENT

```yaml
mac:
  chip: Apple M2
  ram_gb: 8
  shell: zsh            # interactive_comments set by mac.zsh
  project_dir: ~/Desktop/SJSU/cmpe-206-network/project
  code_dir: ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion   # git repo, origin https://github.com/LW1N/tcp-congestion (PUBLIC), separate history from the VM repo (VM tags not carried). Commits: 96851a7 'Bring project to git', 6004ee1 handoff+requirements, 9148bbd 'Add IEEE two-column final report (LaTeX)' (report/ + handoff.md). main == origin/main on 2026-11-09 (pushed). .gitignore excludes results/ data/ figures/ *.pcap __pycache__/ .DS_Store *.pyc *.log. Secret scan clean (sudo passwords in E3.1 are masked). tcp-push does not copy handoff.md/requirements.md/report/ to the VM (explicit rsync list)
  wireshark: installed; tshark at /Applications/Wireshark.app/Contents/MacOS/tshark (used for E5.8, E6.3)
  analysis_venv: GONE (old scratchpad vanished). Rebuild in the session scratchpad: python3 -m venv <scratch>/venv && <scratch>/venv/bin/pip install pymupdf pandas scipy matplotlib pyyaml pypdf. System python3 3.12 has no yaml/pandas/docx; csv module works for data checks
  latex: tectonic 0.17.0 (brew, installed 2026-11-09; XeTeX engine; first run downloads its bundle). No pdflatex/pandoc/Word/LibreOffice on the Mac. System fonts include Times New Roman (/System/Library/Fonts/Supplemental)
  claude_ssh_to_vm: refused from Claude's sandbox ('Permission denied (publickey)' for lucas@vm0.local, 2026-10-24); ask the user to run VM checks, e.g. with the `! <command>` prefix
vm:
  hypervisor: UTM
  os: Ubuntu 26.04.1 LTS ARM64, kernel 7.0.0-38-generic, 4 vCPU, 3.3 GiB visible
  hostname: vm0; user: lucas; ssh alias: tcpvm (works: tcp-push/pull, scp used 2026-10-23)
  project_dir: ~/tcp-congestion   # git repo; canonical notebook.md
  versions: {mininet: 2.3.0, iperf3: 3.20, tshark: 4.6.4, iproute2: 6.19.0, ovs: 3.7.1, python: 3.14.4}
  ccas: [reno, cubic, bbr (v1)]
  disk: 9.8 GB total, 1.4 GB free (86% used) on 2026-10-24; no more experiment runs planned; `sudo apt clean` frees some if needed
  quirk: VM tshark cannot read the pcaps ("permission denied", even with sudo, files are 644 lucas) - cause unconfirmed; run tshark on the Mac and scp results to VM
  system_side_effects: none persistent (host sysctls are per Mininet namespace; r1 ip_forward reset on stop); leftovers after a crash = OVS bridges, veths, stray iperf3/tcpdump/ping -> `sudo mn -c`
  bbr_autoload_at_boot: DONE (/etc/modules-load.d/bbr.conf contains tcp_bbr, checked 2026-10-24); modprobe in bring-up is now redundant but harmless
vm_lifecycle:   # also in guide Step 10 (rev 110)
  teardown: [tmux ls, tmux kill-server, sudo mn -c, 'pgrep -af "mininet|iperf3|tcpdump|run.py|demo.py"  (expect nothing)', sudo poweroff]
  bring_up: ["# Mac: ssh tcpvm 'echo connected to $(hostname)'", "# VM: cd ~/tcp-congestion && sudo -v", sudo mn -c, sudo modprobe tcp_bbr, "sysctl net.ipv4.tcp_available_congestion_control  (expect reno cubic bbr)", quit heavy workloads before the demo]
  demo: ["# VM: cd ~/tcp-congestion && sudo python3 -u demo.py", "# Mac: cap s1 n1-reno sender_h1.pcap  + filter tcp.analysis.duplicate_ack || tcp.analysis.fast_retransmission"]
```

## 4. DOCS (Claude Docs on claude.ai)

| key | url | project_id | tab_file_id | body_node_id | last_known_rev |
| --- | --- | --- | --- | --- | --- |
| proposal | https://claude.ai/artifact/MHnQC8nYRexNPwSauG9wwK | a44ea6f5-2c85-42dd-80ed-b60386cd4e56 | 1fda1f0d-2113 | a6564636-68fa | 65 |
| guide (implementation plan) | https://claude.ai/artifact/BokvUU7o8zuiJZKsWbbiRN | 5782aafa-bbcf-41e2-8797-79b73db5ec59 | 9f63ec6b-914b | 80b14e81-2d18 | 153 |
| report (SUPERSEDED by report/main.tex on 2026-11-09) | https://claude.ai/artifact/7vJiBvAn1QoxLYNaCXatnG | 38082a81-1bd5-4de3-9460-1437f9709115 | e2d990cc-bcbf | 26792df3-7a2c | 69 (4 suggestions accepted) |

```yaml
id_prefixes: {guide: mj7hsvwewd5, report: m2wt2066mr5}   # block ids are <prefix>.<n>
widgets:
  proposal_architecture_diagram: df5ad008-e35c   # pub 6
  report_topology_diagram: 5fdb99cc-093d         # copy of the proposal diagram, subtitle changed
  guide_schedule_timeline: 4aa33b88-6411
enums:
  guide_evidence_status: f2528a45-54f5           # Not captured | Captured | In report
report_blobs:   # uploaded via Artifact publish asset:true to the report URL, then create object=blob. In use at rev 43:
  F2_fairness: 6a35212c-8523        # Figure 2 (legend below, no 'F2.' title prefix, height 2.8)
  F4_s2: c893260d-fd64              # Figure 3 (F18-corrected S2 numbers)
  F5_util: 52aa4c66-bc61            # Figure 4
  F6_share: c32a279d-3962           # Figure 5
  E6.1_late_udp_pfifo: 3d2a9116-4e62   # Figure 6, annotated (arrow at UDP join); old unannotated 89df0a15-9ba7
  diagram: embed node/5fdb99cc-093d    # Figure 1
  unused_old: [6a6dd943-8126 F1, be694870-f019 F2, b4555a94-13e5 F3, 9a0b9e8e-dacb F4, 75eff334-1f43 F5, df3dd58a-4510 F6, d2f4b187-e592 F7, 98d88221-5eb7 F8, 235768c7-25f2 E5.1, 74409043-5ac4 E5.3, d8d9eff2-303e E5.7, adaff7dc-2cbb E6.2, d6cc1064-237c E7.1, bff5743d-dc42 E7.2, 6d563730-087b, 3eb7b0b5-2b64, e44663b6-2b95, 148bf9b5-b6f4, 6c9d851c-704e]
# report_* lines below describe the superseded Claude Doc; see 4c for the live LaTeX report
report_structure: [Abstract, 1 Intro + research question, 2 Background (inline formulas; latex blocks print as raw source in PDF export), 3 Architecture (diagram), 4 Methodology (Platform / Automation and metrics / Validation and limits), 5 Scenarios (Table 1), 6 Results S1-S3 (Figs 2-5), 7 Analysis (Table 2 verdicts; H1, H2+H3, H4 + Fig 6, H5, testbed lessons), 8 Recommendations (Table 3, 6 rows x 3 cols), 9 Conclusion, 10 References 1-16 (verified 2026-10-24 via web search; RFC 3550 and iperf3 added)]
report_page_check: Docs export pdf letter = 8 pages at rev 53 (22 at rev 19). Slack is thin: page 7 ~90 pt free, page 8 ~16 pt; paragraphs split across pages but section headings + following text move together, so a few added lines can push References to page 9. Re-check any edit with export + page count (pymupdf). Pre-rewrite wording recoverable via read atRev 43; old long version atRev 19.
report_style: rewritten 2026-10-24 (revs 44-53) at the user's request so it does not read as AI-generated: varied sentence openings and lengths, no aphoristic 'X: Y' run-in claims (H labels are now 'H1 (utilization).'), some first person ('I measured', 'My first design'), captions not all 'Sx: claim' form. All numbers unchanged. Keep this style in any further edits and in the Step 10 slides.
guide_edits_this_period: {111-117: review fixes in Step 8 verdict table (H3 staggered ~5 Mbps, H4 F18 numbers + jitter, H5 Reno mechanism) and Step 9 rec table (TCP 33-35 / <0.1 Mbps, BBR +0.9, queue delay 28-35 ms at 50 ms and 43-105 ms at 150 ms, up to 105 ms), 118-153: evidence checklist statuses + E9.1 path, 103-106: Step 5 E5.1/E5.2/E5.4/E5.7 expectations + NaN note, 107: E7.4 expectation, 108: Step 8 verdict table filled, 109: Step 9 recommendation table filled, 110: Step 10 VM teardown + bring-up block (mn -c, tmux kill-server, poweroff; ssh check, modprobe tcp_bbr, optional modules-load.d) before "Rehearse twice"}
open_doc_threads:
  - proposal comment on "Stretch goal: a parking-lot extension": user said "unsure yet"; now out of scope (data frozen) - suggest replying "future work"
user_decisions_on_docs:
  - report: references verified 2026-10-24 and the 'cited from memory' note removed; proposal list still carries the note (proposal already submitted, leave)
  - report target: <= 8 pages in the Docs PDF export (letter); no template was given by the user (requirements only say 6-8 pages)
editing_quirks:
  - find targets are case-insensitive; use nth when ambiguous
  - "as":"text" find/replace works for small edits; whole-block replace needs ifHash + ifRev (rev of the READ, not an ack)
  - two inserts after the same anchor in one call are refused (same_anchor)
  - full guide read exceeds tool output; it is saved to a file - parse with python (json -> text, unicode_escape)
  - export tool (format pdf) result is too large for output and is saved to a file: json data.bytes_b64 -> base64-decode to PDF; count pages with pypdf, render pages with pymupdf (helper scripts pdfpages.py and sheet.py in /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/ba0b8331-7fc9-408c-b344-2325bd99d6e5/scratchpad, may vanish)
  - PDF export prints ```latex code blocks as raw TeX; tables render at ~60% page width and tall; images ~0.3-0.4 page each; ~350-400 words per page
  - dropdown chips (e.g. evidence Status) cannot be targeted by id (unknown_id); replace the whole cell: target {kind: cell, table, row, col} + ifRev, with markdown '<?claude block st?>' and blocks {st: {type: dropdown, enum, index}}
  - multi-block replace: target several ids + ifRev alone (no ifHash); a media block is replaced with markdown '![alt](blob/<id>)'
  - a blocks target must be the paragraph id, not a <text> run id (refusal bad_request wrong_kind names the holder block); whole-paragraph replace with as:markdown keeps **bold**/*italic*/`code` that the markdown re-spells (the 'dropped' notices list only the old runs)
  - report PDF helper scripts this session: /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/410e567a-c031-4e3f-9d25-980027b610d9/scratchpad/decode.py <export.txt> <out.pdf> (base64 decode) and /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/410e567a-c031-4e3f-9d25-980027b610d9/scratchpad/layout.py <pdf> (per-page first/last block and bottom y; content area ends ~736 pt on letter)
```

## 4b. SLIDE DECK (Step 10, Slides artifact)

```yaml
url: https://claude.ai/artifact/2GZMMEVvtSyVmNHZ44rzys
type: Slides artifact type (type_url https://claude.ai/artifact/8jTsAFQMFDb2oA8MsPJ2eL, contract 0.2.47); private until the user shares it (Share menu; Claude cannot)
last_published_version: 1794286061-ba86 (version 25, 2026-11-09; Sonnet review fixes: queue colors amber/cyan/violet kept only where they mean pfifo/fq_codel/RED on results + queue labels; verdict rows now white = held up, grey = partly; demo circles white except 4 pink, 5 cyan; layout fixes). v24 1794285687-90fb = FULL RESTYLE to 'Capture Dark' + more animation (see 5e). Before that: 1794279356-0e5c (version 22, review fixes). Earlier: 1792880062-08fe (version 17, 2026-10-24) by Claude; live version on 2026-11-09 is 1794277945-48f3 (changed after Claude's last publish, probably the editor re-save; content reviewed 2026-11-09)
local_files (v24): /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/df40ab0d-e2fa-428c-aada-92e679e3c577/scratchpad/deck-dark/project/ (publish root = .../scratchpad/deck-dark); may vanish -> Artifact read. Older: GONE (old scratchpad 410e567a... vanished). 2026-11-09 copy of version 1794277945-48f3: /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/df40ab0d-e2fa-428c-aada-92e679e3c577/scratchpad/artifact-files/0a453b6c-87ae-4860-be64-30974f20809e/project/  (may vanish too -> Artifact read with paths project/deck.json, project/slides/<id>.html); publish root = that folder's parent
publish: Artifact publish url=<deck>, root=/private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/410e567a-c031-4e3f-9d25-980027b610d9/scratchpad/deck, file_path=<one changed file abs path>, files={"project/slides/x.html": "project/slides/x.html", ...}; send deck.json only when order/sections/faces/title change
order: [cover, problem, compare, topology, implementation, routerfix, scenarios, s1, s2, capture, s3share, s3delay, verdicts, recommendations, demo, close]   # slides 1-16
sections: {intro: cover, design: topology, experiments: scenarios, results: s1, conclusions: verdicts}
faces: [Schibsted Grotesk (text), IBM Plex Mono (labels/eyebrows/data)]   # since v24; was IBM Plex Sans + JetBrains Mono
palette_v24_capture_dark: {bg: '#111019', card: '#1C1B27', card2: '#24223A', rule: '#34324A', text: '#F4F3F7', body: '#C9C7D6', muted: '#A9A7BB', footer: '#8A889C', eyebrow/TCP/RED: '#A78BFA', fq_codel/TCP2: '#4FD1E0', pfifo/TCP3: '#FFB23E', UDP: '#FF5C8A', drop: '#FF6B6B', yes-row: '#13303A', partly-row: '#3A2A12'}   # old light palette below is superseded
  palette_old: {ink: '#14202B', paper: '#F5F4EF', card: '#FBFAF7', rule: '#DCD8CE', body: '#4A5361', muted: '#5F6673', eyebrow: '#1F63B8', accent_slide_bg: '#1D3F6B', fq_codel: '#2A78D6', pfifo: '#EB6834', RED: '#1BAF7A', single_series_bars: '#3E5468'}   # categorical trio validated with dataviz validate_palette.js on #F5F4EF (contrast WARN -> every bar has a value label)
assets: {E6.1_wireshark_late_udp: /_blob/26f9d284fb17188ee7d3b17b017637c2}   # slide 10
live_animations (x-embed canvas, browser only; PDF/PPTX export freezes them; Google Slides cannot run them):
  slide2 problem: 3 TCP + 1 UDP senders -> router queue (12 slots) -> slow link; drops fall; TCP halves on drop, UDP never
  slide3 compare: two embeds - rate-over-time curves for Reno/CUBIC/BBR drawn live (dashed capacity line, orange loss dots); live pfifo / RED / fq_codel queues
  slide4 topology: packets flow h1-h4 -> s1 -> r1 queue strip (10 slots inside r1 box) -> orange bottleneck -> s2 -> h5-h8; drops before r1; white probe dot; appears on build step 6
  slide7 scenarios: one small embed per card (S1 converging TCP flows, S2 dense UDP + dropped TCP, S3 buffer cycling 0.25x/1x/4x BDP)
click_builds (data-build-in on pinned children): topology 1-6, implementation 1-6, scenarios 1-4, s1 1-3, s2 1-4, capture 1-3, s3share 1-4, s3delay 1-4, verdicts 1-5, recommendations 1-3, demo 1-6
charts: hand-built pinned divs from figures/s*_summary.csv (F18-corrected); pixel scales: s1 15 px/%, s2 10 px/Mbps, s3share 6 px/%, s3delay 1.8 px/ms
speaker_notes: every slide, first person, written to R12; base for the E10.3 transcript
render_check: NONE done - type instructions say never verify unless the user asks; layout heights were budgeted by hand (content area y 128-920 with footer, 952 without)
quirks:
  - opening the deck in its editor re-saves (normalizes) slide files; the next publish of such a file is refused until you Artifact-read it. 2026-10-24 conflict on problem.html was only reformatting, replaced intentionally
  - x-embed JS is written with no '<' and no '&' characters (comparisons reversed, nested ifs) to avoid HTML parsing problems; each embed must stay <= 16 KB, be a direct pinned child of <section>, text >= 24px
  - table cells take plain text only (no <b>); pinned text needs a width; at most 200 elements per slide
  - Google Slides route (offered, not chosen): export PPTX, import, overlay GIFs; Claude offered to render the 4 animations as looping GIFs with Python
```

## 4c. FINAL REPORT (LaTeX, live deliverable)

```yaml
source: report/main.tex            # IEEEtran [conference,12pt,letterpaper]; fontspec Times New Roman (fallback TeX Gyre Termes), unicode-math texgyretermes-math.otf
output: report/main.pdf            # 8 pages letter (page 8 ~half full: refs [2]-[16] + Table III), committed in 9148bbd
build: "cd report && tectonic main.tex"   # Overleaf: XeLaTeX compiler (no Times New Roman there -> Termes)
figs: {topology: TikZ in main.tex (Fig 1), F2/F4/F5/F6: report/figs/*.pdf (copies of figures/, which is gitignored), Fig 6: figs/capture_reno_inflight.png (E7.2 cropped, Reno 0.25x BDP 50 ms), Fig 7: figs/capture_late_udp.png (E6.1 cropped, annotated arrow)}
floats: Table I and III and Figs 2-7 are full-width (table*/figure*); Table II and Fig 1 column-width; float fractions raised in preamble
font_sizes: body 12 pt; IEEEtran sets captions, tables, references smaller (UNKNOWN whether the instructor requires 12 pt everywhere; forcing it likely exceeds 8 pages)
references: 16, thebibliography in order of first citation (keys gettys..ware); no BibTeX
page_check: "<venv python> -c \"import pymupdf; print(pymupdf.open('report/main.pdf').page_count)\""   # regex on PDF bytes does not work (object streams)
review_2026-11-09: Sonnet subagent checked every number vs CSVs; fixes applied only in main.tex: Reno 150 ms regrowth '>1 min, most trials never finish a cycle' (s3_ss.csv: no halving between ~2 s and teardown at 66 s; old doc said ~40 s), fq_codel 'best on delay and fairness' + small Reno throughput cost (util 94.4/94.6%), 'single BBR flow' builds no standing queue (n2/n4-equal-bbr-pfifo 37/40 ms), UDP model within 0.1 Mbps for CUBIC+Reno only (BBR +0.8-0.9), BBR 25% UDP loss cause hedged (fq_codel also 3.2%), Jain 'about 0.95 or higher' (n4-equal-bbr-pfifo 0.9496), BBR shortfall 2-4%, Fig 2 'lowest', Table I caption notes 3 late-BBR + 2 late-UDP trials
unverified_text: '±4 ms queue-delay noise' (carried from the old report; not in handoff/notebook; summary CIs ~±1-2 ms)
```

## 5. CODE MAP (`tcp-congestion/`)

| path | role |
| --- | --- |
| topo/shaping.py | (docstring fixed to say router r1, 2026-10-24) bdp_packets; apply_bottleneck (htb root + child pfifo/red/fq_codel; RED min=limit/6, max=limit/2); apply_path (netem delay). |
| topo/dumbbell.py | Topology + config report. `sudo python3 -u -m topo.dumbbell [--cli] [--rate] [--rtt] [--buf-bdp] [--qdisc]`. Router r1, static ARP, offloads off, IPv6 off. Exports IP, bottleneck(net), configure(), start(). |
| traffic/iperf.py | start_server (-1 -J), start_client (TCP -C cca -O omit; UDP -u -b -l 1200; optional start delay). |
| traffic/probes.py | ping -D -i 0.2; ss -tin every 0.1 s; tc -s qdisc every 0.5 s; tcpdump -Z root -s 96 -U. |
| run.py | YAML runner. Flags: --dry-run --only (repeatable) --trials --staggered --udp-delay --capture --resume --seed. Shuffled configs, interleaved trials, idle-RTT check (min, max(10%, 2 ms)), 3 attempts, cleanup() = pkill iperf3/tcpdump/ping + mn -c (so never run two scenarios at once, F15). |
| experiments/s1_competing.yaml, s2_tcp_udp.yaml, s3_buffer_delay.yaml | grids + capture lists (16 captured configs: 6/3/7) |
| analysis/parse.py | -> data/<s>_{flows,trials,series,ss,ping}.csv; newest copy wins per (config, trial); parse_qdisc returns 4-tuples (t, backlog, drops, sent_bytes). Window = time every flow is measured: measured(flow, omit) per flow, window = (max start, min end) = 5-65 s, 5-60 s in S2 (F18); parse_flow(path, flow, window, omit) recomputes a flow measured longer than the window from in_window() intervals, goodput/loss/jitter receiver side from srv_<port>.json; ping/qdisc/wire_mbps use the same window; flows.csv has bytes_sent |
| analysis/metrics.py | utilization = 100*wire_mbps/R (F9), Jain, queue delay, CUBIC share, retrans_pct weighted by bytes_sent (F19), mean + 95% CI -> figures/<s>_summary.csv; check(min_abs_ci=1.0) (F11); --check, --flagged; convergence |
| analysis/plots.py | F1-F8 (PNG + PDF); F4 has 3 panels incl. UDP jitter, F1 titles 2 decimals (F14); titles have no 'Fn.' prefix, F2 legend below the plot, heights F2 2.8 / F4 3.0 / F5 2.7 / F6 2.7 in (2026-10-24, to fit the 8-page report) |
| demo.py | presentation demo, 6 stages, Enter advances; ran OK on VM 2026-10-24 |
| helpers/mac.zsh, helpers/vm.sh | shortcuts (section 6) |
| devtools/gen_fake.py | synthetic results for Mac testing (run in a scratch copy) |
| handoff.md, requirements.md | this file and the course requirements (moved here from the project root 2026-11-09) |
| notebook.md | Mac mirror of the VM notebook (canonical copy on the VM, R8) |
| report/main.tex, report/main.pdf, report/figs/ | final report (section 4c) |

```yaml
topology:
  bottleneck: {node: r1, intf: r1-eth1, direction: r1 -> s2}
  delay: netem on s2 receiver ports; ACK path unshaped
  addresses: {h1-h4: 10.0.0.1-4, hp: 10.0.0.9, h5-h8: 10.0.1.5-8, hr: 10.0.1.10, r1-eth0: 10.0.0.254, r1-eth1: 10.0.1.254}
  mixed_rtts_ms: {2_flows: [20, 80], 4_flows: [20, 40, 60, 80]}
  cubic+bbr_mix: h1, h3 cubic; h2, h4 bbr
results_runs:
  s1: {main: 20261023-002910, staggered: 20261023-045729-staggered, step4_test: 20261023-001006}
  s2: {main: 20261023-062503, late_udp: [20261023-191437-udpdelay20, 20261023-191808-udpdelay20], rerun: 20261023-192941}
  s3: {main: 20261023-222128, rerun: 20261024-022002}
results_path: results/<scenario>/<run>/<config-id>/trial_<k>/
```

## 6. SHORTCUTS (one-time setup DONE)

| name | host | usage | effect |
| --- | --- | --- | --- |
| tcp-push | Mac | `tcp-push` | rsync code to tcpvm:~/tcp-congestion (not evidence/) |
| tcp-pull | Mac | `tcp-pull` | rsync evidence, results, data, figures, notebook.md back; never deletes |
| shot | Mac | `shot step5-s1/E5.1_s1-reno-inflight.png` | move NEWEST ~/Desktop/Screenshot*.png into evidence/ (take the screenshot first) |
| cap | Mac | `cap s2 udp100-cubic-pfifo bottleneck.pcap udpdelay` | open trial-1 capture in Wireshark |
| trial | Mac, VM | `trial s1 n1-reno` | newest trial_1 folder |
| lastblock / maxbacklog / udpq / probertt / done_count | VM | see guide | qdisc/backlog/UDP/RTT summaries; maxbacklog fixed (F13) |
| rerun_flagged | VM | `rerun_flagged s1` | parse, rerun --flagged configs x8, re-parse (F12) |

## 7. FINDINGS (cause -> fix -> status)

| id | symptom (measured) | cause | fix | status |
| --- | --- | --- | --- | --- |
| F1 | UDP through switch-port bottleneck: 48.7 Mbps, 0% loss | skbs keep socket ownership across veth + OVS; queue pushes back on sender; TSQ caps TCP queue | bottleneck moved to router r1 | DONE (V2: 48.4 Mbps, 19% loss; V3: 167p, 16,789 drops). In report §3 |
| F2 | first ping ~82 ms at 40 ms | ARP crosses delayed path | static ARP | DONE |
| F3 | pings 0.3-5 ms above configured delay | VM latency (0.82 ms avg at --rtt 0) + late netem timers | idle-RTT check uses min, max(10%, 2 ms); per-trial idle subtraction | DONE. In report §4 |
| F4 | mininet> commands printed nothing | setLogLevel('warning') | setLogLevel('output') | DONE |
| F5 | pcaps empty (predicted) | tcpdump drops privileges | tcpdump -Z root | DONE |
| F6 | pasted "# comment" fails in zsh | interactive_comments off | setopt in mac.zsh | DONE |
| F7 | rerun_flagged one argument from many IDs | word splitting | array | DONE |
| F8 | --check missed configs with no trials | summary only had data configs | compare with YAML | DONE |
| F9 | goodput 47.8 (TCP) / 48.6 (UDP) at R=50 | htb counts L2 bytes (1514 B per 1448 B segment) | utilization = wire bytes / (R x t) | DONE. In report §4 |
| F10 | saturated link read 98.8% | window included teardown | window ends at last flow end | DONE |
| F11 | udp100-*-pfifo flagged even after 8 trials (2 +/- 0.5 Mbps) | relative CI meaningless near zero | check ignores CI < 1.0 absolute | DONE |
| F12 | second --check after rerun read stale CSVs | rerun_flagged did not re-parse | re-parse at end | DONE |
| F13 | maxbacklog: "too many values to unpack" | parse_qdisc gained 4th value (F9) | `t, b, d, _` | DONE |
| F14 | F4 lacked UDP jitter; F1 titles "+/- 0.0" | plotting gaps | 3rd panel; 2 decimals | DONE |
| F15 | user ran S2 and S3 in parallel | cleanup() kills all iperf3 + mn -c each trial | deleted both, ran sequentially | DONE; rule: one scenario at a time |
| F16 | n1-b0.25-rtt10 Reno/CUBIC util 23% (cwnd median 11 vs BDP 42), BBR 97% | unpaced bursts overflow 11-pkt queue; likely amplified by VM batching | none (result); report caveat | DONE (report §7.1) |
| F17 | udp100 pfifo util 95-96% | UDP stops at 60 s, TCP runs 65 s (-O 5); starved TCP regrows slowly | superseded by F18: with the 5-60 s window util is 99.8-99.9% | DONE (report 'Testbed lessons' now describes F18) |
| F18 | S2 TCP goodput includes 5 s with no UDP: per-second series, TCP while UDP is on vs reported (CUBIC pfifo): udp25 35.3 vs 36.5, udp50 22.9 vs 25.1, udp75 10.7 vs 13.1, udp100 0.02 vs 2.2 Mbps; fq_codel ~34.9 vs 36.1 | UDP client has no -O (runs 0-60 s); TCP runs 0-65 s with summary 5-65 s, so 60-65 s is UDP-free (tail TCP 25-48 Mbps) | recompute S2 TCP metrics over the overlap window 5-60 s from s2_series.csv (no reruns needed); update report §6.2, abstract, Fig 4, rec table, §7.6 | DONE 2026-10-24 on Mac (parse.py overlap window; s2 TCP now 35.5/23.1/10.7/0.05 CUBIC pfifo; S1/S3 summaries unchanged except retrans) |
| F20 | notebook.md had 12 truncated/garbled passages (e.g. '167 maxnsmits', 'Replong bias', 'CUBIC's shrops') | likely text lost during heredoc pastes into the VM terminal (cause UNVERIFIED) | rebuilt from data/context on the Mac 2026-10-24; pre-repair copy /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project/ba0b8331-7fc9-408c-b344-2325bd99d6e5/scratchpad/notebook_before_repair.md | DONE on Mac; VM copy UNVERIFIED (open item 1b) |
| F19 | s2_summary retrans_pct_mean up to 2,365,104% (udp100 pfifo) | retrans_pct = mean of per-flow ratios; starved flow sends ~0 bytes in window (max(bytes,1)) | aggregate: sum(retransmits)*MSS / sum(bytes) per trial; not cited in report text | DONE 2026-10-24 (metrics.py bytes-weighted) |

## 8. STATE (by guide step)

| step | status | notes |
| --- | --- | --- |
| 1 Environment | DONE | E1.1-E1.3 |
| one-time setup | DONE | tcpvm, helpers, Wireshark in use |
| 2 Topology | DONE | router r1 topology; E2.1-E2.4 |
| 3 Validation | DONE | V1-V9 PASS (report §4 table) |
| 4 Automation | DONE | E4.1, E4.2 |
| 5 S1 | DONE | E5.1-E5.8 reviewed; notebook entry present (Mac copy) |
| 6 S2 | DONE | E6.1-E6.5 reviewed; notebook entry present |
| 7 S3 | DONE | E7.1-E7.5 reviewed; notebook entry present; data freeze |
| 8 Analysis | DONE | F1-F8 regenerated 2026-10-24 (F18/F19, titles, sizes); verdict table in guide corrected (rev 117); notebook entry present |
| demo.py dry run | DONE 2026-10-24 | 6 stages OK (fq_codel stage ~16/16/16 Mbps) |
| 9 Report | DONE (user: 'It looks good', 2026-11-09) | IEEE LaTeX report, section 4c; committed + pushed 9148bbd. E9.1_report.pdf still holds the old single-column Docs export (open item 4a) |
| 10 Presentation | IN_PROGRESS | Deck DONE as draft 2026-10-24 (section 4b): 16 slides, visual-first, 4 slides with live animations, click builds, speaker notes on all. Deck UNVERIFIED rendered (nobody has stepped through it in Present mode). TODO: user review in Present mode, share the deck if graders need the link, 2 rehearsals with demo.py (start with VM bring-up), E10.2 recording, E10.3 transcript (start from speaker notes). UNVERIFIED: demo slide stage 3 'CUBIC shrinks' when BBR joins (based on S1 pfifo 10.6% CUBIC share, not on demo.py output) |
| git tags | DONE up to analysis-done; commit/tag for the 2026-10-24 report fixes UNKNOWN (open item 1) | tags: step1-done step2-done step3-done step4-done s1-done s2-done s3-done analysis-done. HEAD 73aa38b Analysis complete; b960f62 S3 data freeze; 06739d6 S2; a1cd65f S1; e3d7f8f Step 4 |

## 9. OPEN_ITEMS (priority order)

0. DONE 2026-11-09: re-review fixes. Deck R1-R5 published (versions 20-22). Report suggestions R1 R6 R7 R8 accepted in the doc (rev 69) and carried into report/main.tex; the doc's re-export step is moot (doc superseded). Historical findings kept for reference: Findings:
   - R1 (deck + report): 'fq_codel's only cost is <1 ms UDP jitter' (deck s2 on-slide text, close notes; report §9 'removed all of these effects at a cost of under 1 ms') ignores Reno's loss under fq_codel: S1 n2/n4-equal-reno util 94.4/94.6% vs 99.9-100% on pfifo; S2 Reno fq_codel 33.2-33.9 vs 35.4 Mbps. Report Table 3 caption already says 'Reno loses about 5%'.
   - R2 (deck verdicts notes): H3 'yes on pfifo, and RED didn't change it' is wrong; under RED BBR wins at every buffer (CUBIC 2.2-2.5%). Report says 'Supported on pfifo, not RED'.
   - R3 (deck s2 footer): 'Reno and BBR within 0.9 Mbps of CUBIC' is true on pfifo only; Reno under fq_codel is ~2 Mbps below.
   - R4 (deck verdicts): H1 'Mostly' vs report 'Partly'.
   - R5 (deck s3share): RED 1x label '2.4%' should be '2.3%' (2.348).
   - R6 (report abstract): 'On a plain FIFO, BBR took 89-99% of the link from CUBIC' omits that at 4x BDP CUBIC took 58.9%; add 'at buffers up to 1x BDP' or similar.
   - R7 (report §6 S1): 'Reno and CUBIC 99.97%': Reno is 99.98%.
   - R8 (requirements gap): 'TCP retransmissions' metric barely appears (only the 21% in the capture). Candidate sentence: on pfifo BBR retransmitted 3.6-10.6% of bytes (S1 n2/n4-equal-bbr) vs CUBIC <= 0.05%. Report page slack is thin (§4 report_page_check): re-export + page count after any addition. Do not cite S2 udp100 pfifo retrans (89-117%, starved-flow artifact).
   - R9 DONE 2026-11-09: .DS_Store untracked and ignored.

1. VM sync: user ran tcp-push + analysis + tcp-pull (2026-10-24 00:33); pulled summaries match the Mac run to 1e-12. UNVERIFIED: VM commit/tag (suggested `git add -A && git commit -m "Report fixes: S2 measurement window, retrans weighting, figure layout" && git tag report-fixes`). Ask the user for `git status --short && git log --oneline | head -3 && git tag | tail -3` output.
1b. DONE on Mac 2026-10-24: notebook.md's 12 garbled passages rebuilt from data/context (pre-repair copy in this session's scratchpad: notebook_before_repair.md, md5 d89e35e39fa111c63a01d77ba345e40f = VM copy as of the 00:33 pull) and a '2026-10-24: Step 9 report review, S2 window fix' entry appended (Surprise 8 = F18, F19 bug, corrections to earlier entries). User was given the guarded copy command with host lucas@vm0.local (R11): `[ "$(ssh lucas@vm0.local 'md5sum < ~/tcp-congestion/notebook.md' | cut -d' ' -f1)" = d89e35e39fa111c63a01d77ba345e40f ] && scp ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion/notebook.md lucas@vm0.local:~/tcp-congestion/notebook.md && echo "copied" || echo "STOP: VM notebook changed since the pull, tell Claude"`, then a VM commit of notebook.md. UNVERIFIED until the user reports 'copied' (if STOP: re-pull, re-apply the repairs and the new entry).
1c. DONE 2026-10-24 (guide rev 153): evidence statuses set. In report: E1.1 E1.3 E2.2 E2.4 E3.2 E4.1 E6.1 E6.3 E7.1 E7.2 E8.1 E8.2 E8.3; Captured: all other E1-E9 (E9.1 path updated); Not captured: E10.1-E10.3. All E1-E9 files verified present in tcp-congestion/evidence/. Statuses are cell-level dropdown chips: change one by replacing the cell (kind cell, table mj7hsvwewd5.50640, col 5) with a new dropdown chip (enum f2528a45-54f5).
2. DONE 2026-10-24: references 1-16 verified (web), note removed from report. Proposal reference list still says 'cited from memory' (proposal is already submitted; leave unless user asks).
3. DONE 2026-10-24: Figure 6 annotated and swapped in.
4. DONE 2026-10-24: E9.1_report.pdf (old Docs export, 8 pages). Superseded by 4a.
4a. TODO: copy the new report into evidence: `cp report/main.pdf evidence/step9-report/E9.1_report.pdf` (from tcp-congestion/), then commit. Also ask the user whether captions/tables/references must be 12 pt too (UNKNOWN). Any report edit -> `tectonic main.tex`, confirm <= 8 pages.
4b. Optional: the superseded Claude Doc report still has the 7 errors listed in 4c review_2026-11-09; fix only if the user still shares that link.
5. Step 10 (IN_PROGRESS). Deck built (section 4b, 16 slides rather than the guide's ~10; extra results slides keep one chart each).
5a. TODO (user): step through the deck in Present mode in a browser; report any overflow, overlap or animation that does not run. Fix by editing the slide file and republishing (section 4b).
5b. TODO: rehearse demo.py twice (VM bring-up block first) and check slide 15's expected values: stage 2 ~48 Mbps, stage 3 CUBIC shrinks, stage 4 TCP ~0, stage 5 ~16 Mbps each (stage 5 seen in the 2026-10-24 dry run; stages 2-4 values UNVERIFIED).
5c. TODO: E10.2 screen recording and E10.3 transcript; then set guide evidence rows E10.1-E10.3 (Not captured -> Captured).
5e. DONE 2026-11-09 (deck v24): user chose 'Capture Dark' and asked for animation wherever possible (audience: students + professor; easy to follow but technical). Applied to all 16 slides: every slide data-transition="magic" with a progress bar (#progress width 104*n px, top 1040) morphing between slides; shared ids tag-s1 (scenarios -> s1), lg-pf/lg-fq legends (s1 -> s2), tag-s3 (s3share -> s3delay); auto build cascades on cover, implementation, close, recommendations leaves; click builds kept for narrated reveals. New x-embed animations: cover (live packet-list capture scroll), routerfix (2 embeds: switch port pauses sender vs router drops), s3delay (CUBIC buffer 70-100% full vs BBR near empty, 50 ms path); recolored: problem, compare x2, topology, scenarios x3 (rewritten). Capture slide image inverted via CSS filter (white = TCP, red = UDP) with build overlays (UDP-join marker, 'TCP starved for 40 s' band). Speaker notes updated for new colors and builds. Checks run: format limits, no '<'/'&' in embed JS, node syntax + 600-frame runtime smoke test of all 11 scripts (0 errors). Known tradeoff left as designed: per-host flow colors (h1 violet, h2 cyan, h3 amber, h4 pink) reuse the queue hues on cover/problem/topology/scenarios slides. UNVERIFIED: rendered look in Present mode (no render check per type rules) and whether 'N auto' build syntax behaves as assumed. Theme exploration history: Blueprint, Transit map rejected; Packet list purples too similar; Capture too dull;  User finds the current palette boring. Rejected: Blueprint, Transit map. Liked Packet list but its purples were hard to tell apart (flow colors worst-pair dE 5). New candidate 'Capture' = Packet list layout (Schibsted Grotesk + IBM Plex Mono, bg #F4F3F7, ink #17161F, packet-row cover, dark #17161F statement/closing slides) with one hue per component: TCP violet #6741D9 / cyan #0089A8 / amber #B86E00, UDP and RED pink #C2255C, pfifo amber #B86E00, fq_codel cyan #0089A8, drop #E03131 (all >= 3:1 on bg; worst pair dE 25 incl. simulated CVD). Comparison page https://claude.ai/artifact/6TZ1ntkudevUbSQQkqxCoG (version 4: Packet list | Capture | Oscilloscope, 8 slides each + measured table); generator scratchpad/themes/gen4.py in session df40ab0d. User then said Capture looked washed out (cause measured: cyan #0089A8 and amber #B86E00 low OKLCH chroma 0.11/0.14). Version 5 adds 'Capture Vivid': bg #FFFFFF, ink #17161F, muted #56546B, flows violet #7048E8 / azure #069CE4 / tangerine #DC7D12 / UDP rose #E8336D, pfifo orange #F3680F, fq_codel azure #069CE4, RED violet, dark slides #141320 with neon accents #FF5C8A #4CC9F0 #FF9F43; each color = max chroma at its hue with >= 3:1 on white; mean chroma 0.181 vs 0.149; worst pair dE 30-31. Generator scratchpad/themes/gen5.py. Version 6 (user asked for a dark variant; dislikes only Oscilloscope's grid): 'Capture Dark' = Packet list layout on plain #111019 (no grid), card #1C1B27, text #F4F3F7, muted #A9A7BB, rule #34324A; flows violet #A78BFA / cyan #4FD1E0 / amber #FFB23E / UDP rose #FF5C8A; pfifo amber, fq_codel cyan, RED violet; drop #FF6B6B; glow on bars; worst pair dE 28/33; columns Capture Vivid | Capture Dark | Oscilloscope (grid removed). Generator gen6.py. Awaiting the user's pick, then restyle all 16 slides + 6 x-embed animations (colors in JS) + deck.json faces.
5d. UNKNOWN: whether the presentation must be in Google Slides. If yes: export PPTX, import, and replace the 4 frozen animations with GIFs (Claude offered to generate them); click builds may not carry over.
6. Reply to proposal parking-lot comment thread: out of scope, future work.
7. DONE 2026-11-09: stale 0-byte project/notebook.md deleted (moving it would have overwritten the real mirror tcp-congestion/notebook.md).
8. Optional: free ~1.1 GB on the VM by deleting ~/tcp-congestion/results after confirming the Mac copy is complete (Mac copy has 514 `done` files, counted 2026-10-24: S1 180 incl. 2 Step-4 test + 3 staggered, S2 146 incl. 2 late-UDP + 24 rerun, S3 188 incl. 8 rerun; VM also has 514 (checked 2026-10-24), so the Mac copy is complete; demo does not need results). User has not asked for the commands yet.

```bash
# Local checks after code changes (Mac, from tcp-congestion/)
python3 -m py_compile topo/*.py traffic/*.py analysis/*.py run.py demo.py
bash -n helpers/vm.sh
zsh -n helpers/mac.zsh
# Analysis on real pulled data (Mac): copy data/ analysis/ experiments/ run.py topo/ to a scratch dir, then
#   <venv python> -m analysis.metrics s1 --check ; <venv python> -m analysis.plots F1 F4
#   (needs pyyaml, pandas, matplotlib, numpy, scipy)

# Report page check (Mac): Docs export pdf letter -> decode data.bytes_b64 -> <venv python> pdfpages.py <export.txt> <out.pdf>  (pypdf page count)

# State checks to ask the user to run
#   VM:  cd ~/tcp-congestion && git status --short && git tag && git log --oneline | head -5 && df -h ~
#   VM:  md5sum ~/tcp-congestion/notebook.md   (after the scp it should be de8672eeddc20e65f1533d8f5205dcee = repaired Mac copy, 340 lines, 2026-10-24)
```

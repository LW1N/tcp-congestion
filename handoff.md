# handoff.md: agent handoff for CMPE 206 TCP congestion project

<!--
Format: optimized for AI agents. Facts are key: value lines or tables with exact identifiers.
Status values: DONE | TODO | IN_PROGRESS | UNVERIFIED | UNKNOWN. UNVERIFIED = implemented but never observed
working where it matters. UNKNOWN = ask the user or check before relying on it.
Last updated: 2026-11-16 (/handoff refresh from a Mac session: RED follow-ups s1r + s2r for S1/S2 approved, written, dry-run, committed 0307ade; runs pending in WSL; deck live version moved to 1794885141-44f9).
-->

## 0. READ_FIRST

1. Read this file, then `requirements.md` (course requirements: report sections, 6-8 pages, rubric 20/20/20/20/10/10).
2. Code and docs are usually edited on the user's Windows PC in WSL2 (`/home/lucas/tcp-congestion`); the 2026-11-16 RED session ran Claude on the Mac repo instead (section 3 mac_claude). Check `pwd` to know which. The live demo runs on the Mac + VM: code reaches the VM via GitHub -> Mac `git pull` -> `tcp-push`. Claude cannot run sudo; the user runs experiments and demo.py and pastes output.
3. Deliverables: report `report/main.pdf` (8 pages, 4c), slide deck (4b, 16 slides; presented from the animated .pptx in Google Slides, 4b pptx_animated), prep guide (4d). All data is in git.
4. Before editing the deck or guide, re-read them (F24, F37): list files, do a bare Artifact read of the url, then read the files you will change, and diff against any local copy. Scratchpad copies from earlier sessions are gone.
5. Highest priority: OPEN_ITEMS #1c (user runs s1r + s2r in WSL and pastes output; check the anchors against the VM before using any RED number), then #1 (user checks the animated .pptx in Google Slides), #1a (build scripts exist only in a scratchpad wiped on WSL restart: RED results will need slides 8/9 rebuilt in the .pptx) and #2 (demo.py dry run with livecap on Mac + VM; never run).
6. Prose rules: R12, R14 (user's voice). Slide rules: R13, R19, R22. Do not trust UNKNOWN items (9, item 3a).

## 1. USER_RULES (must follow)

- R1: Every command complete and copy-pasteable. No placeholders, no "see above".
- R2: Label where each code block runs: `# WSL` (current), `# Mac`, `# VM`, `# mininet>`. Several commands meant to run in order each get their own block.
- R2a: Mininet CLI commands: one per block (Mininet forwards later pasted lines to stdin).
- R3: Prefer helper shortcuts (section 6) where they exist (Mac/VM only).
- R4: SUPERSEDED 2026-11-15: the WSL repo is the working copy, pushed to GitHub by the user.
- R5: When the user pastes terminal output, check it against expectations and look for anomalies (found F9-F14, F21, F22 this way).
- R6: Refer to the user with they/them.
- R7: After code changes run local checks (section 9) and a Sonnet subagent review of the diff (user's global CLAUDE.md). Fix real problems it finds; reject wrong ones with a reason.
- R8: notebook.md canonical copy was on the VM; give entries as heredocs, never overwrite blindly. Which copy is canonical now is UNKNOWN (open item 7).
- R9: Notebook entries hold measured numbers, mechanisms, numbered Surprises, practical notes, Next.
- R10: The VM is shared; never assume it is up or clean (bring-up in section 3).
- R11: Use exactly the host form the user asks for in commands (they once asked for `lucas@vm0.local` instead of `tcpvm`).
- R12: Deliverables must not read as AI-generated: varied sentence openings and lengths, no aphoristic 'Label: claim.' openers, some first person, exact numbers.
- R13: Slides: few on-slide words (~25), visuals preferred, details in speaker notes (<aside>), no H1-H5 labels or config ids on slides, define CCA, RTT, BDP, Jain where first used, easy for an audience seeing it once.
- R14: Prose in the user's voice: reason-first openings, 'This ...' follow-ups, plain words, first person, no semicolons or em dashes. Sample: paragraphs 4-5 of `CMPE 272 Group Reflection.pdf` (on the Mac).
- R15: Report: two-column IEEE, Times New Roman, 12 pt, 6-8 pages (keep at 8).
- R16: Do not start experiment runs; prepare files, dry-run them, give run commands.
- R17: The user commits with messages Claude drafts (no Co-Authored-By trailer). Give multi-line messages as `git commit -F - <<'EOF' ... EOF` (F25).
- R18: Hedge mechanisms that were not measured ("likely", "consistent with"); state cross-machine comparisons as such and mark second-machine results with * on slides.
- R19: Never present an effect built into the setup as a finding (buffers are sized in BDPs, so delay grows with RTT by construction). Normalize instead and say what is by design.
- R20: Slides are critically checked for accuracy and for an audience seeing them once; after slide or guide changes, run a Sonnet review of the diff too.
- R21: A project review covers the published artifacts too (deck, prep guide, the three Claude Docs), not only the repo.
- R23: The talk is shown in Google Slides from an imported .pptx (user, 2026-11-16). Anything put in the .pptx must work there: no embedded video (shows a still, F39); animated GIFs, native entrance effects and fade transitions do work.
- R22: Prefer comparisons the audience can read across (queue x algorithm grids) over highlighting one case; the user rejected a slide built on one CUBIC flow and a delay-only framing (2026-11-16). When a comparison lacks data, propose a targeted follow-up run instead of mixing settings from different experiments.

## 2. PROJECT

```yaml
user: Lucas Nguyen (solo)
course: CMPE 206, SJSU; option: TCP Congestion and Network Performance Analysis; tools: Mininet, iperf3, Wireshark
scenarios: {S1: competing TCP flows + single-flow baseline, S2: 3 TCP + 1 UDP, S3: buffer (router queue size) x delay}
dropped: [random-loss scenario, bandwidth sweep (fixed 50 Mbps), parking-lot topology (future work)]
axes: {cca: [reno, cubic, bbr v1], qdisc: [pfifo, red, fq_codel], buffer_x_bdp: [0.25, 1, 4], rtt_ms: [10..150]}
main_study (VM): {configs: 95, trials: 492, run: 2026-10-23..24}
follow_ups (WSL, own scenario names): {configs: 41 (23 S1, 18 S3), trials: 205; the report counts 29 / 145 because s3q is slides and guide only; 10 configs repeat VM settings, CIs overlap except 5 small gaps (largest 10 ms / 5% loaded RTT at 4x BDP); pending s1r + s2r add 35 configs / 175 trials (not run)}
red_scope_decision (2026-11-16): the main study ran RED only in S3 (2 CUBIC + 2 BBR) with no recorded reason; the user judged that not defensible, so S1 and S2 get full RED grids (s1r, s2r). Report/slide wording waits for the data, not the predictions
framing: loss-based (Reno, CUBIC) vs model-based (BBR v1) vs unresponsive (UDP)
headline: the router queue matters more than the CCA; fq_codel best or tied-best on delay and fairness everywhere (averaged over a setting's flows)
presentation_format: animated .pptx imported into Google Slides (user confirmed 2026-11-16; click steps and transitions seen working there)
schedule: {submission: 2026-12-11 ASSUMED (UNKNOWN), report submitted: UNKNOWN}
```

Hypotheses and verdicts: H1 utilization at >=1x BDP: PARTLY (11-packet buffer at 10 ms collapses Reno/CUBIC to 23%). H2 Reno favors short RTT more than CUBIC: SUPPORTED, BBR favors long RTT. H3 BBR wins shallow buffers, CUBIC recovers in deep: SUPPORTED on pfifo, settles at an even split (F22); RED keeps BBR on top. H4 line-rate UDP starves TCP, fq_codel fixes it: SUPPORTED (0.05 -> 35 Mbps). H5 deep FIFO adds its drain time: CUBIC yes (80-86% full, single flows), Reno partly (64-71%, 41% at 150 ms).

Key numbers (main study, pfifo unless noted): single flow util Reno/CUBIC 99.98/99.97%, BBR 97.5%; queue delay CUBIC 27.9, Reno 22.6, BBR 0.8 ms; CUBIC vs BBR 1+1 10.6%, 2+2 1.9-3.3%, fq_codel 48-50%; S3 2+2 CUBIC 1.4 / 1.8 / 58.9% at 0.25/1/4x (settles ~51% at 4x); 4x single-flow delay CUBIC 34.5/162/494 ms, Reno 28/127/245 at 10/50/150 ms; S2 pfifo TCP 35.5/23.1/10.7/0.05 Mbps, fq_codel ~35. Under fq_codel (F32): Reno/CUBIC flows 1.4-3.7 ms above path, BBR flows 4.4-29 ms (35 ms beside Reno, s1w); 4x mix CUBIC 3 / BBR 26 ms.

| follow-up (scenario, file) | result |
| --- | --- |
| s1w `experiments/s1w_reno_wsl.yaml` | Reno vs BBR 40 ms: 10.0% pfifo, 43.8% fq_codel; Reno vs CUBIC 60 s 47.9 +/- 11% |
| s1x `experiments/s1x_rtt_swap.yaml` | path order swapped (F21): CUBIC on 80 ms vs BBR on 20 ms 46.8% (10.4% other order); Reno 55.6% vs 12.7%; 2+2 BBR wins either order |
| s1l `experiments/s1l_long_reno_cubic.yaml` | Reno vs CUBIC 180 s: Reno 38.0 +/- 4.1% |
| s3w `experiments/s3w_reno_bbr.yaml` | 2 Reno + 2 BBR: 1.9 / 2.3% at 0.25/1x; 4x 55.3% at 60 s |
| slong `experiments/slong_steady_state.yaml` | 180 s reruns (F22): CUBIC vs BBR 4x 51.1%; Reno vs BBR 4x 48.1%; BBR 20 ms vs CUBIC 80 ms 47.0% |
| s3q `experiments/s3q_queue_fill.yaml` | 4 flows each, 4x BDP (834 pkts, 200 ms), 50 ms, 180 s, 60 trials, run 2026-11-16, committed ae671b2. Fill % pfifo/RED/fq_codel: Reno 78/12/0.9, CUBIC 85/15/0.9, BBR 30/26/6.7, CUBIC+BBR 75/23/6.7; steady over 3 min. Probe delay pfifo 162/171/64/159 ms, RED 26/30/56/49. fq_codel flows' own RTT: Reno 2.2, CUBIC 2.4, 4 BBR 13.6, mix CUBIC 2.5 / BBR 23.6. BBR under RED ~48,000 drops/trial, 6.6% resent. Mix pfifo 74.5% vs slong 73%. Fill = mean_backlog_pkts / buffer_pkts from data/s3q_trials.csv (not in the summary CSV) |
| s1r `experiments/s1r_red_competing.yaml` | TODO (not run): S1 grid under RED (n 2/4 x equal/mixed x reno, cubic, bbr, cubic+bbr = 16), plus n2-mixed-bbr+cubic-red and n2-equal-reno+bbr-red (slide 8 starred rows); anchors n4-equal-cubic-pfifo, n4-mixed-reno-pfifo repeat S1. 20 configs, 100 runs, ~2.0 h |
| s2r `experiments/s2r_red_tcp_udp.yaml` | TODO (not run): S2 grid under RED (udp 25/50/75/100 x 3 CCAs = 12); anchors udp25-cubic-pfifo, udp100-cubic-pfifo, udp100-cubic-fq_codel repeat S2 (first S2 runs on WSL). 15 configs, 75 runs, ~1.5 h |

## 3. ENVIRONMENT

```yaml
wsl_pc (current):
  host: Windows PC, AMD Ryzen 5 5600X, 15 GB RAM; Ubuntu 26.04.1 in WSL2, kernel 6.18.58.1-microsoft-standard-WSL2, systemd on
  repo: /home/lucas/tcp-congestion (origin https://github.com/LW1N/tcp-congestion, PUBLIC); last seen at ae671b2; needs `git pull` to 0307ade before the RED runs
  apt: {mininet: 2.3.0-1.1build1, openvswitch-switch: 3.7.1-2, iperf3: 3.20-2, tcpdump: 4.99.6-1, iproute2: 6.19.0, tmux: installed}
  python: system 3.14.4 (has yaml; runner runs under sudo with it); analysis via uv 0.13.7 (~/.local/bin/uv); run ad-hoc scripts from the repo with PYTHONPATH=.
  latex: tectonic 0.17.0 (~/.local/bin); needs Times New Roman via fontconfig (F23)
  modules: not loaded at boot; after every WSL restart run bring_up_wsl
  raw_results: results/ 1.2 GB (s1w, s1x, s1l, s3w, slong, s3q 654 MB), gitignored, only on this PC (no backup)
  limits: sudo needs the user's password; no node/JS engine; no browser (Claude in Chrome not connected; Playwright Chromium download denied by the classifier 2026-11-16): no render checks, no deck export; no LibreOffice; no pdfinfo/pdftoppm, `uv run --with pymupdf` denied by the classifier (page count only, section 9); JS checked by a string/bracket tokenizer that does NOT catch `,,` (F38)
  scratchpad: /tmp/claude-1000/-home-lucas-tcp-congestion/<session>/scratchpad, per session, wiped on WSL restart
  uv_tools_that_work: `uv run --no-project --with pillow==11.3.0 --with imageio-ffmpeg==0.6.0` (Pillow + an ffmpeg binary with libx264/gif); pptx skill validate.py needs `--python 3.12 --with lxml --with defusedxml --with python-pptx`
bring_up_wsl: "# WSL: sudo modprobe -a tcp_bbr sch_htb sch_red sch_fq_codel sch_netem openvswitch && sudo systemctl enable --now openvswitch-switch && cat /proc/sys/net/ipv4/tcp_available_congestion_control   (expect reno cubic bbr)"
long_runs_wsl: "tmux new -s <name>, then sudo python3 -u run.py <yaml> 2>&1 | tee ~/<name>_run.log; keep the PC awake (Windows sleep pauses WSL)"
mac_claude: Claude Code also runs on the Mac (Darwin 25.6.0); `uv run python run.py <yaml> --dry-run` works there (no sudo, no Mininet); scratchpad /private/tmp/claude-501/-Users-lucasnguyen-Desktop-SJSU-cmpe-206-network-project-tcp-congestion/<session>/scratchpad; tectonic there UNKNOWN
mac (demo machine): Apple M2, zsh, repo ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion at 0307ade = origin/main (2026-11-16); results/ 2.6 GB of the main study (46 pcaps); Wireshark at /Applications/Wireshark.app/Contents/MacOS/Wireshark (UNVERIFIED)
vm (original testbed, demo host): UTM, Ubuntu 26.04.1 ARM64, kernel 7.0.0-38-generic, 4 vCPU, 3.3 GiB; host vm0, user lucas, alias tcpvm; ~/tcp-congestion; 1.4 GB free
vm_bring_up: ["# Mac: ssh tcpvm 'echo connected to $(hostname)'", "# VM: cd ~/tcp-congestion && sudo -v && sudo mn -c"]
```

## 4. DOCS (Claude Docs on claude.ai)

| key | url | project_id | body_node_id | last_known_rev | status |
| --- | --- | --- | --- | --- | --- |
| proposal | https://claude.ai/artifact/MHnQC8nYRexNPwSauG9wwK | a44ea6f5-2c85-42dd-80ed-b60386cd4e56 | a6564636-68fa | 65 (2026-11-16) | submitted; open parking-lot comment 9229d96b-b330 |
| guide (implementation plan) | https://claude.ai/artifact/BokvUU7o8zuiJZKsWbbiRN | 5782aafa-bbcf-41e2-8797-79b73db5ec59 | 80b14e81-2d18 | 153 (2026-11-16) | stale (Mac/VM era, no follow-ups) |
| report doc | https://claude.ai/artifact/7vJiBvAn1QoxLYNaCXatnG | 38082a81-1bd5-4de3-9460-1437f9709115 | 26792df3-7a2c | 69 (2026-11-16) | SUPERSEDED by report/main.tex |

Doc quirks: the docs `read` tool is deferred (ToolSearch `select:mcp__1a59c906-04da-521d-bda7-7f71b9f9e01c__read`), call `guide(items=["topic.index"])` first; docs take suggestions; read `{"kind":"view","sinceRev":<rev>}` before editing; whole-block replace needs ifHash + ifRev.

## 4b. SLIDE DECK (Slides artifact)

```yaml
url: https://claude.ai/artifact/2GZMMEVvtSyVmNHZ44rzys   # private until the user shares it
type_url: https://claude.ai/artifact/8jTsAFQMFDb2oA8MsPJ2eL (contract 0.2.47); inline deck (no `format` key): inline styles, data-build-in click steps, no deck.css
last_published: 1794885141-44f9 (seen 2026-11-16 from the Mac); what changed since 1794875688-f02c (the version the .pptx export matches) is UNKNOWN: diff before any deck edit
order: [cover, problem, topology, ccas, queues, scenarios, families, s1, s2, capture, s3share, s3delay, verdicts, recommendations, close, demo]
numbering: footer 'n / 16' (none on cover/close), eyebrow 'NN ·' = n-1, progress bar width 104*n px at top 1040; renumber all three when order changes
edit_flow: Artifact list scope=files -> bare Artifact read of the url (F37) -> Artifact read with paths project/deck.json + project/slides/<id>.html into a fresh folder -> edit -> publish url, root=<folder holding project/>, file_path=<one changed slide>, files={"project/slides/<id>.html": "project/slides/<id>.html", ...}; deck.json only when order/sections change
user_edits_seen: 2026-11-15 reorder (families after scenarios), ccas click text, families 'UDP just keeps going', slide 5 click removed; keep their wording
export: Share › Export (PowerPoint), deck page only (user does it). Observed: NO animations or transitions exported, x-embeds flattened to PNG stills, speaker notes kept, only Schibsted Grotesk embedded (IBM Plex Mono substituted unless installed). Shapes come out in HTML document order (painted div = 1 shape + children; painted div with one text child = 1 shape; one-sided or partial borders = extra line shapes); x-connectors become PNG images
style: Capture Dark (bg #111019, card #1C1B27, text #F4F3F7, muted #A9A7BB, footer #8A889C); pfifo #FFB23E, RED #A78BFA, fq_codel #4FD1E0; drop #FF6B6B; fonts Schibsted Grotesk + IBM Plex Mono
slides_of_note:
  3 topology: 6-click build + strip '95 settings × 5+ runs = 492 runs'; notes: router fix (F1), second machine '205 more runs'
  6 scenarios: notes '205 more runs' incl. the deep-buffer queue test (s3q); strip 'RED in S3' and notes 'only one that tests RED' change once s1r/s2r land
  8 s1: CUBIC/Reno share vs BBR, 5 rows (1+1 same RTT, CUBIC 20 + BBR 80, BBR 20 + CUBIC 80*, 2+2 same RTT, Reno + BBR*); bars left 500, height 34, pfifo top 340/458/576/694/812 (click 1), fq_codel +42 (click 2), ~15 px per % (730 px = 48.7%); dashed 50% line x 1250; delay card 27.9 / 0.8 / 37–40 ms (click 3); card 'Reno vs CUBIC, 3-min runs*' 38 / 62% (click 4). A RED bar per row needs thinner bars or tighter rows
  9 s2: TCP total of 3 CUBIC flows vs UDP 25/50/75/100%; baseline y 820, 10 px per Mbps; pfifo bars x 260/535/810/1085 (click 1), fq_codel +82 (click 2), width 72; cards 'link − UDP' (click 3), 'under 1 ms' jitter (click 4). Room for a third bar per group (pitch 275)
  11 s3share: pfifo 4x bar solid 51%* inside dashed 59%; RED 'BBR still wins'
  12 s3delay (rebuilt 2026-11-16 from s3q): 'The queue decides how full the buffer stays'; 4x3 grid rows Reno/CUBIC/BBR/2 CUBIC + 2 BBR, columns pfifo 440 / RED 900 / fq_codel 1360 px (click 1/2/3), rows top 410/510/610/710, dashed 300x44 outline = full buffer, solid fill 300 px = 100%, label at col+312; legend top 810; footer '*second test machine, 3-minute runs' (width 1440)
  13 verdicts: H1 'Partly · 0.25× at 10 ms fell to 23%'; H5 'Partly · CUBIC 81–86% of it, Reno 41–71%'; notes carry the single-flow 494 ms
  14 recommendations: FIFO boxes Small 'BBR* keeps it busy, Reno doesn't' / About 1× '25–40 ms with 2–4 flows, any algorithm' / Large 'shrink it, CUBIC keeps it 85% full'
  15 close: FIFO 'unfair, deep buffers stay up to 85% full'; fq_codel 'fair everywhere, delay under 4 ms except for BBR'
  16 demo: stages 1-6, click 9 'Questions?'
animations: x-embed canvases on slides 1, 2, 3, 4, 5, 6 (x3), 7 (x2)
embed_rules: no '<' or '&' in embed JS, <= 16 KB each, direct pinned child of <section>, canvas text >= 24 px; <= 200 elements per slide
click_steps: 3:6, 4:1, 5:0, 6:4, 7:3, 8:4, 9:4, 10:3, 11:4, 12:3, 13:5, 14:3, 16:7
render_check: only Python composites of exported shapes/images; never seen in PowerPoint
pptx_export: /mnt/c/Users/lucas/Downloads/TCP Congestion and Network Performance.pptx (user's plain export of 1794875688-f02c, 2026-11-16 16:24)
pptx_animated: /mnt/c/Users/lucas/Downloads/TCP Congestion and Network Performance (animated).pptx (40 MB, 2026-11-16 17:07)
  builds: every data-build-in -> native entrance effect on its mapped shapes; viewer values from the type's app.js: 380 ms ease-out, rise/drop start 48 px below/above, left/right start 72 px to that side, scale from 0.8, pop from 0.5 with overshoot; `auto` steps = After Previous, first 600 ms after arrival, then 520 ms apart; click counts equal click_steps above
  embeds: 10 canvas animations ported line by line from their JS to Python/Pillow, as looping animated GIFs (25 fps, seamless: whole periods or a 1 s crossfade); slide 3 = 5 cropped GIFs over the native diagram, background from the export's connector PNGs
  transitions: fade into slides 2-16 (deck uses magic; Morph not used because it can match unrelated shapes; progress-bar slide lost)
  slide14: three grey elbow arrows replaced by native lines (F40)
  status: click steps + transitions confirmed by the user in Google Slides (MP4 version); GIF version validate.py PASSED, UNVERIFIED in Google Slides; slide 14 fix UNVERIFIED by the user
  build_scripts: /tmp/claude-1000/-home-lucas-tcp-congestion/8da487d3-b204-4604-9bb5-d2087b012a0c/scratchpad/build/ (mapping.py = HTML element -> exported shape with text check; render.py = embed ports -> media/*.gif; build.py = timing XML, GIF pics, slide 14 lines, zip). Input /tmp/claude-1000/-home-lucas-tcp-congestion/8da487d3-b204-4604-9bb5-d2087b012a0c/scratchpad/export/un (unzipped export), /tmp/claude-1000/-home-lucas-tcp-congestion/8da487d3-b204-4604-9bb5-d2087b012a0c/scratchpad/deck/project (deck files). Run: `cd /tmp/claude-1000/-home-lucas-tcp-congestion/8da487d3-b204-4604-9bb5-d2087b012a0c/scratchpad/build && uv run --no-project --with pillow==11.3.0 --with imageio-ffmpeg==0.6.0 python render.py && python3 build.py ../animated.pptx`. Wiped on WSL restart (OPEN_ITEMS 1a)
```

## 4c. FINAL REPORT (LaTeX, live deliverable)

```yaml
source: report/main.tex   # IEEEtran conference 12pt letter; fontspec Times New Roman, fallback TeX Gyre Termes
output: report/main.pdf   # 8 pages; rebuilt and committed 2e29abb (2026-11-16); never rendered here (page count only)
build_wsl: F23, then the page count in section 9 must print 8
page_budget: none left. Only text on the last pages moves the page count (pages 4-6 break early around figures); 2026-11-16 a net -58 character edit still gave 9 pages until the conclusion was trimmed
content_2026-11-16 (F32): abstract 'held Reno and CUBIC flows within 4 ms of the path RTT and BBR flows within 35 ms'; S3 fq_codel 'about 0 for the probe, 3 ms for CUBIC flows and 26 ms for BBR flows'; H5 'BBR flows 4-35 ms, likely because BBR ignores CoDel's drops'; Table III 'Delay <4 ms (BBR <=35); Jain >=0.97'; trims: intro and conclusion caveat sentences (caveats remain in Design Recommendations + Table III caption)
not_in_report: s3q buffer-fill grid (slides and guide only; adding it needs text traded), negative queue-delay explanation
red_touchpoints (after s1r/s2r): abstract 'under three queue disciplines'; Table I S1/S2 grid rows + caption follow-up counts; S1 and S2 Results paragraphs; F2 (S1 Jain) and F4 (S2) need a RED series (plots.py has no follow-up plots yet); Table III rows 'Unresponsive UDP', 'Mixed CCAs or RTTs on a FIFO' (F42), '~1x BDP FIFO'; Design Recommendations caveat 'one RED setting'
UNKNOWN: whether captions/tables/references must also be 12 pt
```

## 4d. PREP GUIDE (plain HTML artifact)

```yaml
url: https://claude.ai/artifact/AMpb8QkfwK4J3n4SqsSi3d   # 'Bottleneck Talk Prep', private
last_published: 1794873612-54fd (version 35, 2026-11-16: s3q table in Reference, third big number 85% -> 0.9% fill, SLIDES 12-15 rewritten, Q&A on RED with/without BBR and the fill table, NOTES re-synced from deck v277)
edit_flow: Artifact read (no path) saves the page to ~/.claude/projects/-home-lucas-tcp-congestion/<session>/tool-results/artifact-4bca7363-<version>.html; Read every line; strip everything up to and including '<body>\n' and the trailing '</body></html>'; edit; publish that file to the url
data_arrays: find by grep, not line number: '^var NOTES=', '^var SLIDES=', '^var QA=', 'var STEPS=', 'var RUBRIC=', 'var METRICS=', 'var MEAS=', 'var GL=', 'var CMDS=', 'var STAGES='
views: Start here, Practice the talk (SLIDES, one entry per slide, timer default 15 min), Q&A (sl: slide number, st:1 starred, f:1 'your call', nos:1 not on slides), Demo, Reference
sync_rule: NOTES = deck speaker notes per slide (split <aside> on <br>, html-unescape, nbsp -> space, strip); keep SLIDES order and sl: numbers in step with the deck
checks: string/bracket balance of the <script> block plus a regex for ',\s*,' and '\[\s*,' (F38)
```

## 5. CODE MAP (`/home/lucas/tcp-congestion`)

| path | role |
| --- | --- |
| topo/dumbbell.py, topo/shaping.py | Mininet dumbbell (router r1, bottleneck r1-eth1, netem on s2 receiver ports); htb + pfifo/red/fq_codel; RED min limit/6, max limit/2, p 0.1, no ecn flag |
| traffic/iperf.py, traffic/probes.py | iperf3 clients/servers; ping, ss, tc, tcpdump probes |
| run.py | YAML runner (`sudo python3 -u run.py <yaml> [--dry-run --only ID --trials N --staggered --udp-delay S --capture --resume DIR]`); `a+b` cca_mix alternates flows, first-named CCA gets h1 and the shortest mixed RTT; a single cca_mix name gives n flows of it |
| experiments/*.yaml | s1/s2/s3 main grids; follow-ups s1w, s1x, s1l, s3w, slong, s3q, s1r, s2r (section 2). Config IDs use only keys written in the grid entry, not defaults: write `qdisc` in every entry |
| analysis/parse.py | results/<scenario> -> data/<scenario>_*.csv; newest copy wins per (config, trial); exits 1 if a scenario has no trials |
| analysis/metrics.py | figures/<scenario>_summary.csv (mean + 95% CI); <first CCA>_share_pct for 'a+b' mixes; --check; expected configs from experiments/<scenario>_*.yaml |
| analysis/plots.py | F1-F8 for s1-s3 only (follow-ups have no plots) |
| demo.py | 6-stage live demo (CUBIC + BBR, UDP 100%, fq_codel switch); per-second block (rate bars, child-queue backlog x/167, ping RTT); tcpdump of r1-eth1 to /tmp/demo.pcap; stage-6 LOSS_FILTER; Ctrl+C-safe cleanup (F30); UNVERIFIED in the VM |
| devtools/gen_fake.py | fake results for pipeline tests (run in a scratch copy: it writes results/) |
| README.md | overview, follow-up table (incl. s3q, s1r, s2r), WSL bring-up, demo + livecap, limitations |
| helpers/mac.zsh, helpers/vm.sh | Mac and VM shell helpers (section 6) |
| report/ | main.tex, main.pdf, figs/ |
| data/, figures/ | tracked CSVs for all 9 scenarios |
| notebook.md, evidence/ | lab notebook (no follow-up entries) and step evidence |

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
| F2-F8 | ARP delay, idle-RTT noise, CLI silent, empty pcaps, zsh comments, word splitting, missing-config check | see git history of this file | fixed | DONE |
| F9 | goodput 47.8 Mbps at 50 Mbps | htb counts L2 bytes | utilization from wire bytes | DONE |
| F10-F14 | teardown in window, near-zero CI flags, stale re-parse, unpack error, plot gaps | analysis bugs | fixed | DONE |
| F15 | parallel S2 + S3 runs | cleanup() kills all iperf3 + mn -c | one scenario at a time | DONE (rule) |
| F16 | 11-packet buffer at 10 ms: Reno/CUBIC 23% util, BBR 97% | unpaced bursts, likely VM batching | reported as a result | DONE |
| F17/F18 | S2 TCP counted 5 s without UDP | UDP 0-60 s, TCP 0-65 s | overlap window 5-60 s | DONE |
| F19 | retrans_pct 2,365,104% | mean of per-flow ratios | bytes-weighted | DONE |
| F20 | notebook.md garbled passages | heredoc pastes into VM terminal (UNVERIFIED cause) | rebuilt on the Mac | DONE on Mac; VM copy UNVERIFIED |
| F21 | mixed-RTT mixes always gave the first-named CCA the 20 ms path | flow_plan assigns CCAs and RTTs in the same order | s1x runs both orders | DONE |
| F22 | 60 s competition shares still moving (4x BDP CUBIC 72.6 -> 50.8%) | deep queue converges slowly | 180 s reruns (slong); minor drift left: S1 n4-mixed-bbr 20 ms flow 6.7% vs ~5% settled | DONE |
| F23 | tectonic fails on WSL: no TeX Gyre Termes | no Times New Roman system font | `cp /mnt/c/Windows/Fonts/times*.ttf <scratch>/fonts/`; fonts.conf with `<include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir><scratch>/fonts</dir>`; `cd report && FONTCONFIG_FILE=<scratch>/fonts.conf tectonic -o <scratch>/rep main.tex`; copy main.pdf | DONE (recreate per session) |
| F24 | publish would overwrite user edits | Slides artifact keeps one live version | read every file you will publish, edit that copy | DONE (rule) |
| F25 | `git commit -m "..."` pathspec error | double quotes in message | `git commit -F - <<'EOF'` | DONE |
| F26 | 'BBR for delay at ~1x BDP if every sender runs BBR' | single-flow evidence only; S1 all-BBR pfifo 37-40 ms | reworded everywhere 2026-11-15 | DONE |
| F27/F32 | fq_codel 'under 12 ms' / '~10 ms' for flows | median-based statistic over all CCAs | report 2e29abb, deck, guide now say Reno/CUBIC <4 ms, BBR up to 35 ms in its own queue (see section 2) | DONE 2026-11-16 |
| F28 | guide card one CUBIC flow 494 ms -> '≈0 with fq_codel' | single-flow runs were pfifo only | replaced (now s3q fill 85% -> 0.9%) | DONE |
| F29 | Wireshark at the router shows no drops; resend may be labelled out-of-order | capture is after the qdisc | stage-6 filter dup_ack OR retransmission OR out_of_order | UNVERIFIED |
| F30 | Ctrl+C during node.cmd() skipped demo cleanup | Mininet sendCmd asserts `not self.waiting` | waitOutput() on waiting nodes, then stop probes, finally net.stop() | DONE (code), UNVERIFIED in VM |
| F31 | slide 12 showed delay by path as if RTT caused it | buffer = 4x BDP grows with RTT by construction | superseded by the s3q fill grid | DONE |
| F33/F34/F35 | slide 5 note for a removed click; stale guide lines; VM idle baseline reads high (negative delays) | text drift; VM ping wake-up latency | fixed in deck v275+ and guide v34+; F34(d) 80 vs 81% left (two methods) | DONE 2026-11-16 |
| F36 | small leftovers | - | evidence E9.1 PDF is the old report (item 4); README line ~72 parse claim; topo/dumbbell.py bottleneck_intf() unused; analysis/metrics.py line 41 `rate` unused; report 'both fell to 23%' (22.8 / 23.6); slide 7 eyebrow says 'Background' in the experiments section | TODO (optional) |
| F37 | deck publish refused twice: "You haven't viewed the latest version" | an Artifact read with `paths` alone does not count as viewing | bare `Artifact read` of the url, then publish | DONE (rule) |
| F39 | animated .pptx showed still images in Google Slides; click steps and transitions worked | Google Slides never plays video embedded in an imported .pptx (shows the poster) | embeds as looping animated GIFs instead of MP4 (R23) | DONE (code), UNVERIFIED in Google Slides |
| F40 | slide 14 grey arrows ran along the FIFO box edge and into the corners of the size boxes | exporter's elbow routing of x-connector route=elbow | native lines: stub (1240,620)->(1290,620), spine x 1290 y 516.5-759.5, arrows (1290->1340) at y 518/638/758; the live HTML deck's rendering of these connectors is UNVERIFIED | DONE in .pptx |
| F41 | first MP4 build: p14:media ext GUID wrong | written from memory | correct `{DAA4B4D4-6D71-4841-9C94-3DE7FCFB9230}` (python-pptx); moot after F39 | DONE |
| F42 | Table III row 'Mixed CCAs or RTTs on a FIFO: fq_codel, not RED' (report/main.tex:263) and 'Unresponsive UDP' rest on no RED data: RED ran only for 2 CUBIC + 2 BBR on equal 50 ms paths | S1/S2 grids omitted RED, no reason recorded; s3q shows RED cuts same-CCA loss-based fill 78-85% -> 12-15%, so RED is not 'like pfifo' outside BBR mixes | s1r + s2r | TODO (runs pending) |
| F38 | guide Q&A array got `},,` (would break the Q&A view); bracket tokenizer passed it | replacement string ended in a comma the original already had | regex check for ',\s*,' and '\[\s*,' before publishing (caught by the Sonnet review) | DONE (rule) |

## 8. STATE

| step | status | notes |
| --- | --- | --- |
| 1-8 environment, topology, validation, automation, S1-S3, analysis | DONE | main study frozen 2026-10-24 |
| follow-ups s1w, s1x, s1l, s3w, slong, s3q | DONE | WSL 2026-11-15/16; data and summaries committed (s3q in ae671b2) |
| follow-ups s1r, s2r (RED in S1/S2) | TODO | YAML committed 0307ade, dry-run on the Mac (20 + 15 configs); not run |
| 9 report | DONE (UNKNOWN whether submitted) | 8 pages, F32 wording committed 2e29abb |
| 10 presentation | IN_PROGRESS | deck 1794885141-44f9 (.pptx from 1794875688-f02c), guide v35; .pptx exported and animated (4b); GIF version UNVERIFIED in Google Slides; demo never run; recording/transcript TODO |
| git | DONE | Mac main at 0307ade = origin/main (2026-11-16); WSL copy still at ae671b2 until pulled; handoff.md edits get committed by the user as 'update handoff'; .pptx files and build scripts are outside the repo |
| review 2026-11-16 | DONE | code, data (--check), report, slides, guide, docs checked; F32-F35 fixed, F36 open |

## 9. OPEN_ITEMS (priority order)

1. TODO (user): import '... (animated).pptx' (4b pptx_animated) into Google Slides as a new copy and present it: GIFs on slides 1-7 move and loop, slide 3 GIF crops line up with wires and r1's queue, slide 14 bracket arrows, click counts (4b click_steps). Problems: user sends screenshots.
1a. UNKNOWN (ask now): save the build scripts (4b build_scripts) in the repo, e.g. devtools/pptx/? They are lost on WSL restart; a later deck edit then needs a re-export and a rewrite of the scripts. Offered once, no answer yet.
1c. TODO (user runs in WSL): RED follow-ups s1r + s2r (section 2, F42). Commands: `# WSL: cd ~/tcp-congestion && git pull` then bring_up_wsl, then `sudo python3 -u run.py experiments/s1r_red_competing.yaml --dry-run && sudo python3 -u run.py experiments/s2r_red_tcp_udp.yaml --dry-run` (expect 20 and 15 configurations), then in `tmux new -s red`: `cd ~/tcp-congestion && sudo python3 -u run.py experiments/s1r_red_competing.yaml 2>&1 | tee ~/s1r_run.log && sudo python3 -u run.py experiments/s2r_red_tcp_udp.yaml 2>&1 | tee ~/s2r_run.log`, then `for s in s1r s2r; do uv run python -m analysis.parse $s && uv run python -m analysis.metrics $s --check; done`. Next for Claude: compare anchors with the VM rows in figures/s1_summary.csv (n4-equal-cubic-pfifo, n4-mixed-reno-pfifo) and figures/s2_summary.csv (udp25-cubic-pfifo, udp100-cubic-pfifo, udp100-cubic-fq_codel); then draft report (4c red_touchpoints), slides 6/8/9/13/14 and guide changes from the data; then .pptx rebuild (1a). Predictions, NOT results (R18): CUBIC+BBR under RED ~2% as in S3; same-CCA loss-based flows lower delay than pfifo; Reno mixed-RTT bias possibly smaller; TCP beside UDP unknown
1b. Optional, if the live HTML deck is still used: check whether its slide 14 elbow connectors look like F40 and fix the x-connector routes there.
2. TODO (user runs, Mac + VM): `# Mac: cd ~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion && git pull && tcp-push && source helpers/mac.zsh`, then `# VM: cd ~/tcp-congestion && sudo mn -c && sudo python3 -u demo.py`, then at stage 1 `# Mac: livecap`. Build the Wireshark I/O graph once, save as profile 'demo' (tcp.dstport==5201, tcp.dstport==5202, udp.dstport==5204; bits; 100 ms). Expected: stage 2 ~48 Mbps, queue ~65-167/167, ping ~68 ms; 3 CUBIC falls toward ~5; 4 TCP ~0, ping ~73; 5 ~16 each, ping ~40. Check the stage-6 filter finds packets (F29) and the in-place redraw in Terminal.app. Dry-run twice; paste output (R5).
3. DONE 2026-11-16: F32-F35 fixed; report committed 2e29abb; s3q run, slide 12 rebuilt, committed ae671b2; all pushed.
3a. UNKNOWN (ask): talk length (prep timer default 15 min, deck 16 slides), whether the report was already submitted, the deadline (2026-12-11 assumed), whether captions/tables must be 12 pt, whether to trade report text for the s3q result.
4. TODO: copy the final report into evidence: `cp report/main.pdf evidence/step9-report/E9.1_report.pdf`, then commit (the evidence copy predates 2e29abb).
5. TODO: rehearse twice with the prep guide, then E10.2 screen recording and E10.3 transcript (from speaker notes); set guide evidence rows E10.1-E10.3.
6. TODO (optional): back up WSL results/ (1.2 GB) outside WSL.
7. TODO: notebook entries for the follow-ups incl. s3q (R9); decide with the user which notebook copy is canonical.
8. Optional, only if the user asks: F36 leftovers; report figure fonts too small (F4 axis/legend ~5 pt, F6 legend over fq_codel bars; analysis/plots.py, no page room); bandwidth sweep, RED/ECN variants (future work).
9. Old, low priority: VM commit/tag after 2026-10-24 fixes UNVERIFIED; repaired notebook not copied to the VM; reply 'future work' to the proposal parking-lot comment; free ~1.1 GB on the VM (delete results/, Mac copy complete).

```bash
# WSL: code checks (syntax only; __pycache__ is root-owned so py_compile fails)
cd ~/tcp-congestion && python3 -c "import ast,glob; [ast.parse(open(f).read(),f) for f in glob.glob('topo/*.py')+glob.glob('traffic/*.py')+glob.glob('analysis/*.py')+['run.py','demo.py']]; print('ok')"
```

```bash
# WSL: data checks for every scenario, on a throwaway copy (metrics rewrites figures/)
rm -rf /tmp/tcpcheck && mkdir /tmp/tcpcheck && cd ~/tcp-congestion && cp -r run.py analysis experiments data figures topo /tmp/tcpcheck/ && cd /tmp/tcpcheck && for s in s1 s2 s3 s1w s1x s1l s3w slong s3q; do uv run --project ~/tcp-congestion python -m analysis.metrics $s --check; done
```

Expected: 'all configurations OK' nine times (add s1r s2r to the loop once they have data; then eleven). Regenerated s1-s3 summaries differ from the committed ones only in the last float digits (generated on the Mac/VM), so never commit a regenerated figures/s{1,2,3}_summary.csv.

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

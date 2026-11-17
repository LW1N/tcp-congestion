# handoff.md: agent handoff for CMPE 206 TCP congestion project

<!--
Format: optimized for AI agents. Facts are key: value lines or tables with exact identifiers.
Status values: DONE | TODO | IN_PROGRESS | UNVERIFIED | UNKNOWN. UNVERIFIED = implemented but never observed
working where it matters. UNKNOWN = ask the user or check before relying on it.
Last updated: 2026-11-16 (Mac session: RED follow-ups now use `ared`, a 5 ms-target Adaptive RED (F45); red1x dropped; s1r, s2r, s3r, s3qr written and dry-run, uncommitted; runs pending in WSL; post-run docs plan is OPEN_ITEMS 1f).
-->

## 0. READ_FIRST

1. Read this file, then `requirements.md` (course requirements: report sections, 6-8 pages, rubric 20/20/20/20/10/10).
2. Code and docs are usually edited on the user's Windows PC in WSL2 (`/home/lucas/tcp-congestion`); the 2026-11-16 RED session ran Claude on the Mac repo instead (section 3 mac_claude). Check `pwd` to know which. The live demo runs on the Mac + VM: code reaches the VM via GitHub -> Mac `git pull` -> `tcp-push`. Claude cannot run sudo; the user runs experiments and demo.py and pastes output.
3. Deliverables: report `report/main.pdf` (8 pages, 4c), slide deck (4b, 16 slides; presented from the animated .pptx in Google Slides, 4b pptx_animated), prep guide (4d). All data is in git.
4. Before editing the deck or guide, re-read them (F24, F37): list files, do a bare Artifact read of the url, then read the files you will change, and diff against any local copy. Scratchpad copies from earlier sessions are gone.
5. Highest priority: OPEN_ITEMS #1c (user checks `adaptive` on WSL, then runs s1r + s2r + s3r + s3qr and pastes output), then #1f (docs update from the RED data, step by step), #1 (user checks the animated .pptx in Google Slides), #1a (build scripts exist only in a scratchpad wiped on WSL restart: RED results will need slides rebuilt in the .pptx) and #2 (demo.py dry run with livecap on Mac + VM; never run).
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
follow_ups (WSL, own scenario names): {configs: 41 (23 S1, 18 S3), trials: 205; the report counts 29 / 145 because s3q is slides and guide only; 10 configs repeat VM settings, CIs overlap except 5 small gaps (largest 10 ms / 5% loaded RTT at 4x BDP); pending s1r, s2r, s3r, s3qr add 45 configs / 225 trials (not run)}
red_scope_decision (2026-11-16): the main study ran RED only in S3 (2 CUBIC + 2 BBR) with no recorded reason; the user judged that not defensible, so S1 and S2 get full RED grids (s1r, s2r). Report/slide wording waits for the data, not the predictions. 2026-11-16 (user approved): every RED follow-up uses `ared` (F45), and every RED number in the report and slides comes from ared; the old `red` data (S3, s3q) is kept and cited only as a check
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
| s1r `experiments/s1r_red_competing.yaml` | TODO (not run): S1 grid under ared (n 2/4 x equal/mixed x reno, cubic, bbr, cubic+bbr = 16), plus n2-mixed-bbr+cubic-ared and n2-equal-reno+bbr-ared (slide 8 starred rows); anchors n4-equal-cubic-pfifo, n4-mixed-reno-pfifo repeat S1. 20 configs, 100 runs, ~2.0 h |
| s2r `experiments/s2r_red_tcp_udp.yaml` | TODO (not run): S2 grid under ared (udp 25/50/75/100 x 3 CCAs = 12); anchors udp25-cubic-pfifo, udp100-cubic-pfifo, udp100-cubic-fq_codel repeat S2 (first S2 runs on WSL). 15 configs, 75 runs, ~1.5 h |
| s3r `experiments/s3r_ared_buffer.yaml` | TODO (not run): S3's 2 CUBIC + 2 BBR at 50 ms, 0.25/1/4x BDP, 60 s, under ared and pfifo; the 3 pfifo configs repeat S3 (same-machine baseline for ared; VM fq_codel stays cross-machine). 6 configs, 30 runs, ~0.6 h |
| s3qr `experiments/s3qr_ared_queue_fill.yaml` | TODO (not run): s3q's 4 mixes at 4x BDP, 50 ms, 180 s under ared (F43); s3q supplies pfifo/red/fq_codel on the same machine. 4 configs, 20 runs, ~1.1 h |

## 3. ENVIRONMENT

```yaml
wsl_pc (current):
  host: Windows PC, AMD Ryzen 5 5600X, 15 GB RAM; Ubuntu 26.04.1 in WSL2, kernel 6.18.58.1-microsoft-standard-WSL2, systemd on
  repo: /home/lucas/tcp-congestion (origin https://github.com/LW1N/tcp-congestion, PUBLIC); last seen at ae671b2; needs `git pull` to the commit with ared (after the user commits this session's work) before the RED runs
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
red_touchpoints: see OPEN_ITEMS 1f (post-run docs plan, with main.tex lines)
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
| topo/dumbbell.py, topo/shaping.py | Mininet dumbbell (router r1, bottleneck r1-eth1, netem on s2 receiver ports); htb + pfifo/red/ared/fq_codel; red: min limit/6, max limit/2, p 0.1, no ecn flag (unchanged since the main study); ared: Adaptive RED, min = max(5 pkts, 2.5 ms at the link rate) = 15625 B at 50 Mbps, max = 3 x min = 46875 B, burst 19, `probability 0.1 adaptive` (kernel adapts max_p 1-50% every 0.5 s toward an average queue between min + 0.4 and min + 0.6 of the range, ~5 ms), limit = buffer (>= 1.7 x max, at 0.25x BDP 50 ms), no ecn; ARED_TARGET_MS = 5 |
| traffic/iperf.py, traffic/probes.py | iperf3 clients/servers; ping, ss, tc, tcpdump probes |
| run.py | YAML runner (`sudo python3 -u run.py <yaml> [--dry-run --only ID --trials N --staggered --udp-delay S --capture --resume DIR]`); `a+b` cca_mix alternates flows, first-named CCA gets h1 and the shortest mixed RTT; a single cca_mix name gives n flows of it |
| experiments/*.yaml | s1/s2/s3 main grids; follow-ups s1w, s1x, s1l, s3w, slong, s3q, s1r, s2r, s3r, s3qr (section 2). Config IDs use only keys written in the grid entry, not defaults: write `qdisc` in every entry |
| analysis/parse.py | results/<scenario> -> data/<scenario>_*.csv; newest copy wins per (config, trial); exits 1 if a scenario has no trials |
| analysis/metrics.py | figures/<scenario>_summary.csv (mean + 95% CI); <first CCA>_share_pct for 'a+b' mixes; --check; expected configs from experiments/<scenario>_*.yaml |
| analysis/plots.py | F1-F8 for s1-s3 only (follow-ups have no plots) |
| demo.py | 6-stage live demo (CUBIC + BBR, UDP 100%, fq_codel switch); per-second block (rate bars, child-queue backlog x/167, ping RTT); tcpdump of r1-eth1 to /tmp/demo.pcap; stage-6 LOSS_FILTER; Ctrl+C-safe cleanup (F30); UNVERIFIED in the VM |
| devtools/gen_fake.py | fake results for pipeline tests (run in a scratch copy: it writes results/) |
| README.md | overview, follow-up table (incl. s3q, s1r, s2r, s3r, s3qr), ared note, limitations 'Two RED settings', WSL bring-up, demo + livecap, limitations |
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
| F43 | RED delay at 4x BDP looks like a result but is mostly the thresholds: s3q 4 Reno / 4 CUBIC mean backlog 96-100 / 121-123 pkts, just under min_th 139 pkts (~34 ms), probe 25-26 / 30 ms; fill 12/15% ~ min_th/limit = 1/6. fq_codel's 5 ms target is fixed, RED's thresholds scale with the buffer, so the 4x delay comparison is unfair to RED (R19) | thresholds = limit/6, limit/2 | s3qr with ared (F45; red1x dropped before any run) | TODO (runs pending) |
| F45 | `red` targets a delay that grows with the buffer (1x BDP 40 ms: ~6.7-20 ms; 4x 50 ms: 34-100 ms) while fq_codel targets 5 ms, and its limit is only 2x max_th (tc-red: limit a few times max); red1x only half fixed it (thresholds still follow the RTT) | thresholds as fractions of the buffer | `ared` (topo/shaping.py): Adaptive RED (Floyd, Gummadi, Shenker 2001) with fq_codel's 5 ms target, same hard limit as pfifo/fq_codel; used by s1r, s2r, s3r, s3qr; `red` kept for the existing data. R19: ared's delay near 5 ms for loss-based flows is by construction; findings are utilization, fairness, loss, and whether it holds 5 ms with BBR present | UNVERIFIED (never run; `adaptive` untested on the WSL kernel) |
| F44 | notebook.md S3 says RED 4x '368 drops'; data/s3_trials.csv and raw tc show 10,641-11,844 per trial (all 'early', pdrop 0) | UNKNOWN (likely a windowed or wrong-line read) | correct the notebook line with item 7 | TODO |
| F46 | ared Reno util 83-87% and a stronger RTT bias could come from the RED setting, not RED itself | tc picked ewma W = 1/16 from the man-page burst formula (ARED paper: ~0.00024), so drops start whenever the instant queue passes ~10 pkts | user chose option B (2026-11-17): `ared_slow` (topo/shaping.py) = ared with burst 201 so tc picks Wlog 12 (w_q 0.000244); follow-ups s1rs (8 configs), s2rs (2), s3qrs (2), 12 configs / 60 runs ~1.5 h | DONE 2026-11-17: the fast average is NOT the cause. ared_slow (commit 1aa11a8, tc `ewma 12`) locks out: slow start overfills the queue, the slow average climbs past max_th, RED drops every arrival while the queue sits empty, and the average decays only per arrival (likely because Linux restarts idle decay only on dequeue; from memory of sch_red, UNVERIFIED). s3qrs Reno: every attempt failed (all flows 0 Mbps, iperf3 control socket closed; no data). s1rs Reno trials stall 5-64 s with ~250 tail drops at 1x; CUBIC 3-6 s; s3qrs CUBIC trial 1 85 s. Last-30-s comparison (35-65 s, goodput util, same machine) ared vs ared_slow: Reno n2 equal 82.9 vs 67.1, n4 equal 87.6 vs 62.9, CUBIC n2 95.3 vs 88.2, n4 96.7 vs 86.8; mixed Jain Reno 0.726 vs 0.689 (n2), 0.741 vs 0.737 (n4), CUBIC 0.794 vs 0.761, 0.777 vs 0.765; udp25 TCP util Reno 68.5 vs 56.0, CUBIC 75.9 vs 66.3. So the ared util cost and RTT bias stand; they follow from the 5 ms target, not the averaging. s1rs/s2rs/s3qrs parsed (s1rs --check flags n4-equal-reno-ared_slow CI 51%, expected; s3qrs stopped by the user after 2 CUBIC trials, Reno none, --check fails by design, README notes it); user chose (2026-11-17): option A wording plus one ared_slow sentence and the 1/RTT model sentence; commit the ared_slow data; report cites s1rs/s2rs only; lockout mechanism only in notes/guide (hedged) |
| F38 | guide Q&A array got `},,` (would break the Q&A view); bracket tokenizer passed it | replacement string ended in a comma the original already had | regex check for ',\s*,' and '\[\s*,' before publishing (caught by the Sonnet review) | DONE (rule) |

## 8. STATE

| step | status | notes |
| --- | --- | --- |
| 1-8 environment, topology, validation, automation, S1-S3, analysis | DONE | main study frozen 2026-10-24 |
| follow-ups s1w, s1x, s1l, s3w, slong, s3q | DONE | WSL 2026-11-15/16; data and summaries committed (s3q in ae671b2) |
| follow-ups s1r, s2r, s3r, s3qr (RED as ared) | TODO | s1r/s2r YAML committed 0307ade with qdisc red, switched to ared 2026-11-16; s3r rewritten (file renamed from s3r_red_fixed_thresholds.yaml), s3qr new; dry-run on the Mac 20 + 15 + 6 + 4 configs; uncommitted until the user commits; not run |
| 9 report | DONE (UNKNOWN whether submitted) | 8 pages, F32 wording committed 2e29abb |
| 10 presentation | IN_PROGRESS | deck 1794885141-44f9 (.pptx from 1794875688-f02c), guide v35; .pptx exported and animated (4b); GIF version UNVERIFIED in Google Slides; demo never run; recording/transcript TODO |
| git | DONE | Mac main at 0307ade = origin/main (2026-11-16); WSL copy still at ae671b2 until pulled; handoff.md edits get committed by the user as 'update handoff'; .pptx files and build scripts are outside the repo |
| review 2026-11-16 | DONE | code, data (--check), report, slides, guide, docs checked; F32-F35 fixed, F36 open |

## 9. OPEN_ITEMS (priority order)

1. TODO (user): import '... (animated).pptx' (4b pptx_animated) into Google Slides as a new copy and present it: GIFs on slides 1-7 move and loop, slide 3 GIF crops line up with wires and r1's queue, slide 14 bracket arrows, click counts (4b click_steps). Problems: user sends screenshots.
1a. UNKNOWN (ask now): save the build scripts (4b build_scripts) in the repo, e.g. devtools/pptx/? They are lost on WSL restart; a later deck edit then needs a re-export and a rewrite of the scripts. Offered once, no answer yet.
1c. TODO (user runs in WSL): RED follow-ups s1r + s2r + s3r + s3qr (section 2, F42, F43, F45). WSL pulled to 139ea6a and dry runs checked (20/15/6/4) 2026-11-16; adaptive check PASSED on WSL 2026-11-16 (`tc -d` shows `adaptive ewma 4 probability 0.1`). Runs 2026-11-16/17: s1r DONE (100/100, results/s1r/20261116-211402), s3r DONE (30/30, results/s3r/20261116-232123), s3qr started 23:58 (results/s3qr/20261116-235820), s2r SKIPPED by `sudo: timed out` (per-file sudo in the loop; rerun chained after s3qr with one `sudo bash -c`). Gate 1f(a) passed for s1r + s3r: every ared qdisc.txt contains `adaptive` (`tc -s` prints it without -d). Future long loops: wrap the whole loop in one `sudo bash -c '...'`. First `# WSL: cd ~/tcp-congestion && git pull`, then bring_up_wsl, then the adaptive check: `sudo ip link add redtest type dummy && sudo tc qdisc add dev redtest root red limit 250500 min 15625 max 46875 avpkt 1500 burst 19 bandwidth 50mbit probability 0.1 adaptive && tc -d qdisc show dev redtest; sudo ip link del redtest` (expect a red line containing `adaptive`; if tc errors, stop and fix ared before running). Dry runs: `for f in s1r_red_competing s2r_red_tcp_udp s3r_ared_buffer s3qr_ared_queue_fill; do sudo python3 -u run.py experiments/$f.yaml --dry-run | head -1; done` (expect 20, 15, 6, 4 configurations; ~2.0 + 1.5 + 0.6 + 1.1 h). Run in `tmux new -s red`: `cd ~/tcp-congestion && for f in s1r_red_competing s2r_red_tcp_udp s3r_ared_buffer s3qr_ared_queue_fill; do sudo python3 -u run.py experiments/$f.yaml 2>&1 | tee ~/${f%%_*}_run.log; done` (~5.2 h), then `for s in s1r s2r s3r s3qr; do uv run python -m analysis.parse $s && uv run python -m analysis.metrics $s --check; done`. Then OPEN_ITEMS 1f. Predictions, NOT results (R18): BBR still takes most of the link from CUBIC under ared (one shared queue, BBRv1 ignores loss up to ~20%); ared holds loss-based delay well below pfifo; Reno mixed-RTT bias possibly smaller; TCP beside UDP unknown
1d. DONE 2026-11-16: RED review from the Mac; s3r approved and written. Verified sound: RED never tail-dropped (pdrop 0 in all 15 S3 RED trials), mean backlog between min_th and max_th, drop rate 4-10% with BBR present, CUBIC share consistent with the Mathis rate at that drop rate (fairness result not a misconfiguration). Not fair: delay at 4x (F43). s3r added; s1r/s2r unchanged (at 1x BDP 40 ms their thresholds are ~6.7 and ~20 ms, close to a delay-based setting). (Superseded 2026-11-16 by F45: user approved ared for every RED follow-up.) Not needed then: max_p, adaptive RED, ECN (BBRv1 ignores marks), single flows (fq_codel was not tested there either), more trials (RED CIs: share +/-0.1-0.3 pp, delay +/-1.4 ms).
1e. UNKNOWN (user deciding, 2026-11-16): scenario review. Gap A (recommended): AQMs never ran with single flows or at 10/150 ms, yet Table III says 'fq_codel, any CCA' and the conclusion says its cost is 'up to 5.5% of Reno'. The report's H1 model with fq_codel's ~5 ms standing queue (b ~ 5/RTT BDP) predicts a lone Reno flow at ~80% at 50 ms, CUBIC ~92% (estimates, not results; 4-flow Reno measured 94-95% because flows desync). Proposed s3a: n1 x rtt 10/50/150 x reno/cubic/bbr x fq_codel/ared at 1x BDP, 60 s (matches S3), plus pfifo anchors n1 reno rtt 10/50/150 b1: 21 configs, 105 runs, ~2.1 h (fq_codel only: 12 configs, ~1.2 h). Cheap completions: n2-equal-reno+cubic-red in s1r as n2-equal-reno+cubic-ared (every S1 mix then has all three queues; +5 runs); capture trial 1 of n2-equal-cubic+bbr-ared (Wireshark evidence of RED's mechanism). Optional, previously dropped by the user: bandwidth (only possible-scenario 4 half not covered; would test packet-count effects like F16), random loss (stays dropped).
1g. RESULTS 2026-11-17: all four RED follow-ups run and parsed, --check OK (s1r 100, s2r 75 results/s2r/20261117-010316, s3r 30, s3qr 20 trials; no retries; adaptive in every ared qdisc.txt, pdrop 0 in every ared trial). data/ + figures/ CSVs uncommitted (commit drafted for the user). Step 1f(c) tables shown to the user; wording NOT decided (open questions: how to state ared's utilization cost and its stronger RTT bias). s2r: UDP 100% TCP total CUBIC 2.1 / Reno 2.4 / BBR 7.0 Mbps (pfifo VM 0.1, fq_codel ~35), UDP loss 7.6-17.5%: ared does NOT fix starvation (H4 stays fq_codel-only); UDP 25-75% TCP close to pfifo (Reno 30.8/20.4/10.4, CUBIC 34.0/22.4/10.9, BBR 36.5/26.1/15.9) at probe delay 0.3-2.4 ms loss-based, 6.0-7.1 ms BBR (pfifo 23-37); Reno util 90.3% at UDP 25%. Anchors: WSL udp25/udp100 cubic pfifo and udp100 fq_codel match VM. s3qr (4x BDP, 50 ms, 180 s) fill % Reno/CUBIC/BBR/mix ared 0.3/0.4/2.7/2.3 (pfifo 78/85/30/75, red 12/15/26/23, fq_codel 0.9/0.9/6.7/6.7); probe delay 0.2/0.6/5.7/4.6 ms; util Reno 86.0%, CUBIC 96.2%; mix CUBIC share 2.4% (red 2.6, pfifo 53.4, fq_codel 48.4); 4 BBR ~103k drops/trial, 14% resent. ared probe delay vs fq_codel flows' own RTT are different metrics, do not compare directly. s1r + s3r: Gate 1f(a): adaptive in every ared qdisc.txt, pdrop 0 in every s1r ared trial. Anchors 1f(b): WSL pfifo repeats match VM within CIs (n4-equal-cubic 35.5 vs 34.1 ms; n4-mixed-reno Jain 0.885 vs 0.878; s3r pfifo 0.25/1/4x 11.2/46.9/164.6 ms vs 9.2/45.7/164.4). Results vs predictions: (1) BBR still wins under ared, CONFIRMED and stronger than pfifo: CUBIC 5.2% (pfifo 10.6), Reno 4.9%, n4 CUBIC 2.9-3.1%, BBR on 20 ms vs CUBIC on 80 ms CUBIC 2.2% (pfifo s1x 46.8%); s3r CUBIC 2.4-2.5% at every buffer. (2) Loss-based delay far below pfifo, CONFIRMED, but below the 5 ms target (probe 0.1-0.9 ms, mean backlog 1.7-4.6 pkts vs target ~21) at a utilization cost: Reno 83-87%, CUBIC 94-97% (fq_codel VM 94-98, pfifo 100); likely early drops from min_th (~10 pkts) act like a ~0.06x BDP buffer. (3) Reno mixed-RTT bias smaller: WRONG, larger: Jain Reno 0.75/0.73 (n2/n4), CUBIC 0.78/0.79 vs pfifo VM 0.95/0.88 and 0.99/0.95; likely because an empty queue leaves the raw 20/80 ms ratio (4x) while pfifo's ~28 ms queue shrinks it to ~2.3x (hedge, R18). (4) New: BBR-only mixed RTT Jain 0.99/0.96 vs pfifo 0.80/0.74. (5) With BBR present ared holds probe delay 4.4-6.0 ms at every buffer (s3r 4.6/4.4/4.8 at 0.25/1/4x; old red 1.3/13.2/47.8; pfifo 11/47/165), with retrans 10-15% (pfifo 3-11%); BBR rides max_th (max backlog ~33 pkts, max_th 31). R19: ared's ~5 ms with BBR is its target by design.
1h. VERIFIED 2026-11-17 from raw files (independent script, not analysis/; lost with the scratchpad): util, Jain, TCP Mbps, probe delay match the summary CSVs in all 45 configs; all trials commit 139ea6a, WSL kernel, done marker, no iperf3 errors; all 725 TCP data sockets ran the intended CCA (ss + iperf3 sender_tcp_congestion; the `cubic` seen in ss is iperf3's control socket); s3qr trials that overlapped Claude's parse (23:58-00:17) match the rest; UDP loss recomputed from raw JSON matches. CORRECTIONS to 1g: (a) 'BBR wins more than on FIFO' holds only for 2-flow mixes, same machine: CUBIC 10.9 -> 5.2% (s1w), Reno 10.0 -> 4.9% (s1w), CUBIC on 80 ms vs BBR on 20 ms 46.8 -> 2.2% (s1x), CUBIC on 20 ms 10.4 -> 7.0% (s1x); with 4 flows ared ~ pfifo (s1x n4-mixed 1.8 vs 3.1; s3r 0.25/1x 1.6/2.2 vs 2.4/2.5); at 4x pfifo settles 51-54% vs ared 2.4%. (b) ared probe delay with BBR is 4.4-6 ms only for all-BBR and 4-flow mixes; 2-flow mixes 0.9-2.6 ms (mean backlog 6.7-10 pkts). With BBR the mean backlog sits in the adaptive band (18.8-22.9 pkts) and max ~34 = max_th, so adaptation works under load. (c) Same-machine anchors: Reno util ared 86.0 vs fq_codel 95.0 (s3qr vs s3q); RTT bias Reno n4 Jain ared 0.735 vs pfifo 0.888 (both s1r); everything else vs VM is cross-machine (R18). (d) RTT-bias model: share ~ 1/measured srtt (ss) predicts Jain 0.740/0.770 (Reno n2/n4 ared, measured 0.747/0.735), 0.743/0.775 (CUBIC, measured 0.782/0.790), 0.910 (Reno n4 pfifo WSL, measured 0.888); shares follow the path order in every Reno/CUBIC ared trial; BBR does not follow it (0.99 vs model 0.78). (e) SETTING CAVEAT (new, F46): tc derived ewma Wlog 4 (W = 1/16) from burst 19 (tc-red man-page burst formula), so ared's average tracks the instantaneous queue; ARED's paper recommends w_q ~ 1-exp(-1/C) ~ 0.00024 at 4167 pkt/s. Reno/CUBIC queues stay far below the target band (mean 1.7-4.6 pkts, above min_th only 3-12% of samples, max 13-23), so the utilization cost and the RTT-bias size are properties of this setting; do not call it ARED as published without saying so. Follow-up approved 2026-11-17 (F46): s1rs/s2rs/s3qrs under ared_slow. After the runs: compare util, Jain (mixed), mean backlog, pdrop (slow average may let the 1x BDP queue tail-drop) and probe delay against s1r/s2r/s3qr, then return to the wording choice (A scope wording, C delay-only) with the result.
1f. TODO (Claude, after 1c's data is parsed): update the docs from the RED data, in this order. Every RED number in the report and slides comes from ared; old `red` (S3, s3q) appears only as one check line ('BBR still won and delay followed the thresholds'), never as a co-equal series. Mark WSL numbers * on slides (R18); follow R19 (ared's ~5 ms for Reno/CUBIC alone is its target, not a finding).
  a. Gate (data sanity): `grep -L adaptive results/s{1r,2r,3r,3qr}/*/*ared/trial_*/qdisc.txt` prints nothing; per ared config, pdrop ~0, mean backlog near 21 pkts (5 ms) for loss-based mixes; note where BBR pushes it past max_th (46875 B = 31 pkts) even with max_p at 50%. qdisc.txt comes from `tc -s qdisc show` without -d; that red's printer shows `adaptive` there is UNVERIFIED, so if the grep lists files, check one run by hand (`tc -d qdisc show dev r1-eth1` in the Mininet CLI with --qdisc ared) before concluding. If adaptive really is missing, ared ran as plain RED with p 0.1: report that, do not use the data.
  b. Anchors: pfifo/fq_codel repeats vs VM rows in figures/s1_summary.csv (n4-equal-cubic-pfifo, n4-mixed-reno-pfifo), s2_summary.csv (udp25-cubic-pfifo, udp100-cubic-pfifo, udp100-cubic-fq_codel), s3_summary.csv (n4-b{0.25,1,4}-rtt50-cubic+bbr-pfifo); also s3r 4x pfifo (60 s) vs s3q (180 s, same machine). Gaps outside the CIs get stated as cross-machine in text.
  c. Summarize for the user before editing: a table per scenario (pfifo / ared / fq_codel; share, Jain, delay, util, loss), what changed vs predictions, which hypothesis verdicts move (H3 'not RED', Table III rows). User decides wording.
  d. Figures (analysis/plots.py, writes figures/; report uses report/figs/F2, F4, F5, F6): add 'ared' to QDISC_COLOR/QDISC_STYLE (RED colour #D55E00, label 'RED'); F2 (S1 Jain) gets a RED series from s1r, F4 (S2) from s2r, F6 (CUBIC vs BBR) swaps S3's red for s3r's ared. plots.py reads only s1-s3 today; load the follow-up CSVs next to them, legend notes second machine. Copy the PDFs to report/figs.
  e. Report (report/main.tex; page budget is zero, every addition needs a trim, rebuild with F23 and check 8 pages): line 58 Background add how RED is set (5 ms target like fq_codel, adaptive max_p, same buffer) and a new bibitem for ARED (Floyd, Gummadi, Shenker 2001); Methods / Table I line ~140 S1 and S2 rows add RED, S3 row 'RED' -> ared, caption follow-up counts (report counts 29 configs / 145 trials now; s1r+s2r+s3r add 41 / 205; s3qr stays slides-only like s3q unless text is traded); S1 and S2 Results paragraphs; S3 lines 170-184 (F6 caption 'RED leaves CUBIC near 2%'); H3 verdict line 204; Table III line 263 'Mixed CCAs or RTTs on a FIFO: fq_codel, not RED' plus rows 'Unresponsive UDP' and '~1x BDP FIFO' (F42); abstract 'under three queue disciplines'; Design Recommendations caveat 'one RED setting'.
  f. Deck (re-read first, F24/F37; R13 word limits): slide 6 strip 'RED in S3' and notes 'only one that tests RED'; slide 8 a RED bar per row (thinner bars or tighter rows, geometry in 4b); slide 9 a third bar per group (pitch 275 has room); slide 11 RED bar from s3r; slide 12 RED column from s3qr (footer '*second test machine'); slide 13 verdicts; slide 14 if Table III changes; speaker notes say how RED was set and why (F45). Sonnet review (R20), then .pptx rebuild (1a) and re-export.
  g. Guide (4d): Q&A 'why this RED' (target, adaptive, same buffer as fq_codel; old red's thresholds grew with the buffer), Reference s3q table gains an ared column, SLIDES/NOTES resynced from the deck. Sonnet review (R20).
  h. README (Main finding line if it changes; follow-up table already lists s3r/s3qr), notebook.md entry for the RED runs plus the F44 correction, data/ and figures/ summaries committed, commit messages drafted (R17), this handoff updated (F42, F43, F45 statuses).
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
rm -rf /tmp/tcpcheck && mkdir /tmp/tcpcheck && cd ~/tcp-congestion && cp -r run.py analysis experiments data figures topo /tmp/tcpcheck/ && cd /tmp/tcpcheck && for s in s1 s2 s3 s1w s1x s1l s3w slong s3q s1r s2r s3r s3qr; do uv run --project ~/tcp-congestion python -m analysis.metrics $s --check; done
```

Expected: 'all configurations OK' thirteen times with s1r s2r s3r s3qr added to the loop (all have data since 2026-11-17). s1rs/s2rs/s3qrs are left out on purpose: ared_slow lockouts make their CI checks fail (F46). Regenerated s1-s3 summaries differ from the committed ones only in the last float digits (generated on the Mac/VM), so never commit a regenerated figures/s{1,2,3}_summary.csv.

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

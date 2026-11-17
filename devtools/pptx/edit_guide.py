"""Update the prep guide for the RED follow-ups; NOTES re-synced from the edited .pptx."""
import json, re, sys
from lxml import etree

SRC, PPTX_UN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(SRC, encoding='utf8').read()
s = s[s.index('<body>\n') + len('<body>\n'):s.rindex('</body></html>')]   # page body only

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'


def deck_notes(n):
    root = etree.parse(f'{PPTX_UN}/ppt/notesSlides/notesSlide{n}.xml').getroot()
    for sp in root.iter(P + 'sp'):
        ph = sp.find('.//' + P + 'ph')
        if ph is not None and ph.get('type') == 'body':
            tx = sp.find(P + 'txBody')
    lines, cur = [], ''
    for p in tx.findall(A + 'p'):
        for ch in p:
            if ch.tag == A + 'r':
                cur += ch.findtext(A + 't') or ''
            elif ch.tag == A + 'br':
                lines.append(cur); cur = ''
        lines.append(cur); cur = ''
    lines = [l.replace(' ', ' ').strip() for l in lines]
    while lines and not lines[-1]:
        lines.pop()
    return lines


notes = [deck_notes(n) for n in range(1, 17)]
i = s.index('var NOTES=')
j = s.index(';\n', i)
s = s[:i] + 'var NOTES=' + json.dumps(notes, ensure_ascii=False) + s[j:]


def sub(old, new):
    global s
    assert s.count(old) == 1, ('count', s.count(old), old[:90])
    s = s.replace(old, new)


# ---------- Start view ----------
sub('pfifo → fq_codel; RED 15% (follow-up*, slide 12)',
    'pfifo → fq_codel; RED* 0.4%, its 5 ms target (slide 12)')
sub('<div class="card"><h4>Demo stages 2–4 not yet seen</h4>',
    '<div class="card"><h4>RED is one tuning</h4><p class="small">Every RED number on the slides is RED aimed at fq_codel’s 5 ms (second machine). A slower average, as the ARED paper recommends, was worse: drops locked flows out for seconds. Say the numbers are for that setting.</p></div>\n'
    '      <div class="card"><h4>Demo stages 2–4 not yet seen</h4>')

# ---------- Reference ----------
sub('<tr><td>Late-start runs</td><td class="num">3 BBR + 2 UDP</td></tr>',
    '<tr><td>Late-start runs</td><td class="num">3 BBR + 2 UDP</td></tr>\n      <tr><td>Follow-up runs, 2nd machine*</td><td class="num">482 (incl. 277 RED)</td></tr>')
sub('Ten original settings re-run there matched the VM within the confidence intervals apart from five small gaps, the largest a 10 ms (5%) lower loaded RTT at 4× BDP.</p>',
    'Eighteen original settings re-run there matched the VM within the confidence intervals apart from small gaps, the largest a 10 ms (5%) lower loaded RTT at 4× BDP.</p>')
sub('''      <p class="small muted">Reno’s 20 and 80 ms flows have effective RTTs (with queue) of 49 and 109 ms, so the short one regrows about twice as fast.</p>
    </div>
  </section>''',
    '''      <p class="small muted">Reno’s 20 and 80 ms flows have effective RTTs (with queue) of 49 and 109 ms, so the short one regrows about twice as fast.</p>
    </div>
  </section>

  <section class="card">
    <h3>RED follow-up* · RED aimed at fq_codel’s 5 ms (slides 8, 9, 11, 12)</h3>
    <div class="tbl-wrap"><table>
      <thead><tr><th></th><th class="num" style="color:var(--amber)">pfifo</th><th class="num" style="color:var(--violet)">RED*</th><th class="num" style="color:var(--cyan)">fq_codel</th></tr></thead>
      <tbody>
        <tr><td>CUBIC vs 1 BBR, same RTT</td><td class="num">10.6%</td><td class="num">5.2%</td><td class="num">48.7%</td></tr>
        <tr><td>Reno vs 1 BBR, same RTT</td><td class="num">10.0%*</td><td class="num">4.9%</td><td class="num">43.8%*</td></tr>
        <tr><td>CUBIC 80 ms vs BBR 20 ms</td><td class="num">46.8%*</td><td class="num">2.2%</td><td class="num">46.9%</td></tr>
        <tr><td>Mixed-RTT Jain, Reno 2 / 4 flows</td><td class="num">0.95 / 0.88</td><td class="num">0.75 / 0.73</td><td class="num">0.97 / 0.99</td></tr>
        <tr><td>Mixed-RTT Jain, CUBIC 2 / 4 flows</td><td class="num">0.99 / 0.95</td><td class="num">0.78 / 0.79</td><td class="num">1.00 / 1.00</td></tr>
        <tr><td>Link use, Reno alone 2–4 flows</td><td class="num">~100%</td><td class="num">83–87%</td><td class="num">94–98%</td></tr>
        <tr><td>TCP beside UDP 25/50/75/100%</td><td class="num">35.5 / 23.1 / 10.7 / 0.05</td><td class="num">34.0 / 22.4 / 10.9 / 2.1</td><td class="num">~35</td></tr>
        <tr><td>CUBIC vs BBR, 2+2, 0.25 / 1 / 4× BDP</td><td class="num">1.4 / 1.8 / 51*</td><td class="num">2.4 / 2.5 / 2.4</td><td class="num">~48</td></tr>
      </tbody>
    </table></div>
    <p class="small muted">RED here: thresholds at 2.5 and 7.5 ms of queue, the kernel adapts max_p (1–50%), same hard limit as the other queues. Delay: Reno and CUBIC alone 0.1–0.9 ms; with BBR 0.9–2.6 ms (2 flows) to 4.4–6 ms (4 flows or all BBR), at every buffer size; BBR resent 10–15%. UDP at 100% lost 7.6–18%. Same machine: Reno 86% under RED vs 95% under fq_codel (4 flows, 4× BDP). A model with each flow’s rate ∝ 1 / its measured RTT predicts the RED Jain (0.74 vs 0.75 for 2 Reno). With the ARED paper’s slow average instead: flows locked out for 5–64 s after slow start, Reno 63–82% even in the last 30 s. pfifo and fq_codel columns are the main study unless starred.</p>
  </section>''')
sub('<span style="color:var(--violet)">RED 48 ms</span>',
    '<span style="color:var(--violet)">RED* 4.8 ms (first RED setting 48 ms)</span>')
sub('<tr><td>Reno</td><td class="num">78%</td><td class="num">12%</td><td class="num">0.9%</td></tr>',
    '<tr><td>Reno</td><td class="num">78%</td><td class="num">0.3%</td><td class="num">0.9%</td></tr>')
sub('<tr><td>CUBIC</td><td class="num">85%</td><td class="num">15%</td><td class="num">0.9%</td></tr>',
    '<tr><td>CUBIC</td><td class="num">85%</td><td class="num">0.4%</td><td class="num">0.9%</td></tr>')
sub('<tr><td>BBR</td><td class="num">30%</td><td class="num">26%</td><td class="num">6.7%</td></tr>',
    '<tr><td>BBR</td><td class="num">30%</td><td class="num">2.7%</td><td class="num">6.7%</td></tr>')
sub('<tr><td>2 CUBIC + 2 BBR</td><td class="num">75%</td><td class="num">23%</td><td class="num">6.7%</td></tr>',
    '<tr><td>2 CUBIC + 2 BBR</td><td class="num">75%</td><td class="num">2.3%</td><td class="num">6.7%</td></tr>')
sub('Delay on pfifo: Reno 162, CUBIC 171, BBR 64, mix 159 ms. RED: 26, 30, 56, 49 ms.',
    'Delay on pfifo: Reno 162, CUBIC 171, BBR 64, mix 159 ms. RED (5 ms target): 0.2, 0.6, 5.7, 4.6 ms, so its low fill is by design (5 ms ≈ 21 packets ≈ 2.5% of this buffer), and Reno used only 86% of the link. The first RED setting, thresholds tied to the buffer, kept it 12, 15, 26, 23% full (26, 30, 56, 49 ms).')
sub('BBR under RED lost ~48,000 packets per run (6.6% of bytes resent).',
    'Four BBR flows under the 5 ms RED lost ~103,000 packets per run (14% resent).')
sub('Reno mixed RTTs 0.88 · CUBIC mixed 0.95 · BBR mixed 0.74.</p>',
    'Reno mixed RTTs 0.88 · CUBIC mixed 0.95 · BBR mixed 0.74 · under RED* Reno 0.73–0.75, CUBIC 0.78–0.79.</p>')
sub('Here min = 1/6, max = 1/2 of the limit."]',
    'Main study: min = 1/6, max = 1/2 of the limit. Follow-ups: adaptive RED aimed at 5 ms (thresholds 2.5 and 7.5 ms of queue, max_p adapted by the kernel)."]')
sub('''{l:"1 CUBIC + 1 BBR, same RTT",b:[["pfifo",10.6,A,"10.6%"],["fq_codel",48.7,Cy,"48.7%"]]},
 {l:"1 + 1, 20 / 80 ms",b:[["pfifo",10.4,A,"10.4%"],["fq_codel",50.4,Cy,"50.4%"]]},
 {l:"2 CUBIC + 2 BBR, same RTT",b:[["pfifo",3.3,A,"3.3%"],["fq_codel",48.9,Cy,"48.9%"]]},
 {l:"2 + 2, 20–80 ms",b:[["pfifo",1.9,A,"1.9%"],["fq_codel",49.5,Cy,"49.5%"]]}''',
    '''{l:"1 CUBIC + 1 BBR, same RTT",b:[["pfifo",10.6,A,"10.6%"],["RED*",5.2,V,"5.2%"],["fq_codel",48.7,Cy,"48.7%"]]},
 {l:"1 + 1, 20 / 80 ms",b:[["pfifo",10.4,A,"10.4%"],["RED*",7.0,V,"7.0%"],["fq_codel",50.4,Cy,"50.4%"]]},
 {l:"2 CUBIC + 2 BBR, same RTT",b:[["pfifo",3.3,A,"3.3%"],["RED*",2.9,V,"2.9%"],["fq_codel",48.9,Cy,"48.9%"]]},
 {l:"2 + 2, 20–80 ms",b:[["pfifo",1.9,A,"1.9%"],["RED*",3.1,V,"3.1%"],["fq_codel",49.5,Cy,"49.5%"]]}''')
sub('''{l:"UDP at 25%",b:[["pfifo",35.5,A,"35.5"],["fq_codel",35.3,Cy,"35.3"]]},
 {l:"UDP at 50%",b:[["pfifo",23.1,A,"23.1"],["fq_codel",35.2,Cy,"35.2"]]},
 {l:"UDP at 75%",b:[["pfifo",10.7,A,"10.7"],["fq_codel",35.1,Cy,"35.1"]]},
 {l:"UDP at 100%",b:[["pfifo",0.05,A,"0.05"],["fq_codel",35.1,Cy,"35.1"]]}''',
    '''{l:"UDP at 25%",b:[["pfifo",35.5,A,"35.5"],["RED*",34.0,V,"34.0"],["fq_codel",35.3,Cy,"35.3"]]},
 {l:"UDP at 50%",b:[["pfifo",23.1,A,"23.1"],["RED*",22.4,V,"22.4"],["fq_codel",35.2,Cy,"35.2"]]},
 {l:"UDP at 75%",b:[["pfifo",10.7,A,"10.7"],["RED*",10.9,V,"10.9"],["fq_codel",35.1,Cy,"35.1"]]},
 {l:"UDP at 100%",b:[["pfifo",0.05,A,"0.05"],["RED*",2.1,V,"2.1"],["fq_codel",35.1,Cy,"35.1"]]}''')
sub('["RED",2.2,V,"2.2%"]', '["RED*",2.4,V,"2.4%"]')
sub('["RED",2.3,V,"2.3%"]', '["RED*",2.5,V,"2.5%"]')
sub('["RED",2.5,V,"2.5%"]', '["RED*",2.4,V,"2.4%"]')

# ---------- prep steps and demo checklists: the talk runs from the .pptx in Google Slides ----------
sub('{t:"Step through the deck once in Present mode",m:"5 min · browser",href:"https://claude.ai/artifact/2GZMMEVvtSyVmNHZ44rzys",b:"Open deck"}',
    '{t:"Import ‘TCP Congestion and Network Performance (RED).pptx’ into Google Slides and click through it once",m:"5 min · Google Slides",go:"#talk",b:"Practice"}')
sub('"Step through the deck once in <b>Present</b> mode in a browser. The live animations and click builds have never been seen rendered; PDF/PPTX export freezes them.",',
    '"Click through the RED deck once in Google Slides <b>Present</b> mode: slides 8 and 9 now have a RED click between pfifo and fq_codel.",')
sub('"Deck open in the browser in Present mode; terminal and Wireshark one switch away. Terminal font large.",',
    '"Deck open in Google Slides in Present mode; terminal and Wireshark one switch away. Terminal font large.",')

# ---------- SLIDES ----------
sub('"Follow-ups on a second machine (WSL): 205 runs, marked * on the results slides; 10 repeated settings matched the VM."',
    '"Follow-ups on a second machine (WSL): 482 runs incl. the RED tests, marked * on the results slides; 18 repeated settings matched the VM."')
sub('"RED (Random Early Detection): drops a few packets at random before it’s full, as an early warning.",',
    '"RED (Random Early Detection): drops a few packets at random before it’s full, as an early warning. Set to aim for 5 ms of queue, like fq_codel.",')
sub('· RED in S3 · 5+ runs per setting. S2 sketch',
    '· RED in all three (2nd machine) · 5+ runs per setting. “+ RED” chip on every card. S2 sketch')
sub('"S3: buffer from 0.25 to 4× BDP and path from 10 to 150 ms. The only one with RED.",',
    '"S3: buffer from 0.25 to 4× BDP and path from 10 to 150 ms.","RED in all three, on the second machine, aimed at the same 5 ms as fq_codel.",')
sub('"+205 follow-up runs, 2nd machine"', '"+482 follow-up runs, 2nd machine"')
sub('{sec:"results",title:"On a FIFO, BBR usually takes the link",clicks:"4",w:1.2,',
    '{sec:"results",title:"On FIFO or RED, BBR usually takes the link",clicks:"5",w:1.2,')
sub('against BBR, pfifo then fq_codel; side:', 'against BBR, pfifo, then RED*, then fq_codel; side:')
sub('"Bottom row: Reno does no better, 10.0% against BBR. Starred rows ran later on the second machine from slide 3, after checking it matched the original runs.",',
    '"Bottom row: Reno does no better, 10.0% against BBR. Starred rows ran later on the second machine from slide 3, after checking it matched the original runs.","[click] Violet (RED*, second machine): worse than the FIFO with one flow of each. CUBIC 5.2%, Reno 4.9%, and 2.2% when BBR has the short path. RED drops from both; only the loss-based flow slows down.",')
sub('"Different RTTs: Reno favors the short path; BBR favors the long one (fits BBR sizing sending from its own RTT).",',
    '"Different RTTs: Reno favors the short path; BBR favors the long one (fits BBR sizing sending from its own RTT).","Under RED (notes): the short path’s advantage grows, Jain ~0.75 for Reno and 0.78 for CUBIC, likely because the near-empty queue leaves the 20 vs 80 ms gap; delay under 1 ms, but Reno loses 13–17% of the link.",')
sub('"Reno vs BBR 10.0 / 43.8%",', '"Reno vs BBR 10.0 / 43.8%","RED* 5.2 / 7.0 / 2.2 / 2.9 / 4.9%",')
sub('{sec:"results",title:"On a FIFO, TCP gets only what UDP leaves",clicks:"4",w:1.2,',
    '{sec:"results",title:"On FIFO or RED, TCP gets only what UDP leaves",clicks:"5",w:1.2,')
sub('screen:"Bars: TCP total at UDP 25/50/75/100%, pfifo then fq_codel;',
    'screen:"Bars: TCP total at UDP 25/50/75/100%, pfifo, then RED*, then fq_codel;')
sub('"[click] Cyan (fq_codel): TCP flat at ~35 no matter how hard UDP pushes.',
    '"[click] Violet (RED*): no help. 34.0 / 22.4 / 10.9, then 2.1 at full speed: UDP ignores RED’s early drops just like the FIFO’s.","[click] Cyan (fq_codel): TCP flat at ~35 no matter how hard UDP pushes.')
sub('nums:["35.5 / 23.1 / 10.7 / 0.05","fq_codel 35.1–35.3",',
    'nums:["35.5 / 23.1 / 10.7 / 0.05","RED* 34.0 / 22.4 / 10.9 / 2.1","fq_codel 35.1–35.3",')
sub('RED callout: “BBR still wins”. Footer: *second test machine, 3-minute runs."',
    'RED* bars from the second machine (5 ms target). RED callout: “RED*: BBR still wins”. Footer: *second test machine · 51%: 3-minute runs."')
sub('"[click] Violet (RED, Random Early Detection): expected early drops to even things out. They don’t: RED drops from both, only CUBIC listens.",',
    '"[click] Violet (RED*, Random Early Detection, 5 ms target, second machine): expected early drops to even things out. They don’t: 2.4–2.5% at every size (my first RED setting gave the same, 2.2–2.5%). RED drops from both, only CUBIC listens.",')
sub('"RED 2.2 / 2.3 / 2.5%"', '"RED* 2.4 / 2.5 / 2.4%"')
sub('Values 78/12/0.9, 85/15/0.9, 30/26/7, 75/23/7%.', 'RED column header “RED · 5 ms target”. Values 78/0.3/0.9, 85/0.4/0.9, 30/2.7/7, 75/2.3/7%.')
sub('"[click] RED: Reno or CUBIC alone 12–15%, because they back off on its early drops. With BBR 23–26%, likely because BBR ignores the drops.",',
    '"[click] RED (5 ms target): nearly empty by design, 5 ms ≈ 21 packets ≈ 2.5% of this buffer. Reno and CUBIC stay under it (0.3, 0.4%) and Reno pays with 86% of the link. With BBR it sits at the target (2.7, 2.3%), likely because BBR ignores the early drops. First RED setting: 12–26%.",')
sub('"RED 12 / 15 / 26 / 23%"', '"RED* 0.3 / 0.4 / 2.7 / 2.3% (by design)"')
sub('"2 · Reno favors short paths more than CUBIC: yes. Its 20 ms flow regrows ~2× faster. BBR favors the long path."',
    '"2 · Reno favors short paths more than CUBIC: yes. Its 20 ms flow regrows ~2× faster. BBR favors the long path. Under RED the bias got stronger (Reno Jain ~0.75)."')
sub('"4 · Full-speed UDP starves TCP, fq_codel fixes it: clearly yes (0.05 → 35 Mbps)."',
    '"4 · Full-speed UDP starves TCP, fq_codel fixes it: clearly yes (0.05 → 35 Mbps). RED doesn’t fix it (TCP ~2 Mbps)."')
sub('"RED isn’t a substitute: CUBIC still ~2% against BBR."',
    '"RED isn’t a substitute, even aimed at fq_codel’s 5 ms: CUBIC ~2% against BBR, TCP ~2 Mbps beside full-speed UDP, Reno loses 13–17% of the link. A slower RED average was worse."')
sub('"Caveat: one 50 Mbps link in a VM → directions, not exact numbers."',
    '"Caveat: one emulated 50 Mbps link, BBRv1, no ECN → directions, not exact numbers."')
sub('"Across almost 500 runs, the router’s queue mattered more than the sender’s algorithm."',
    '"Across almost a thousand runs on two machines, the router’s queue mattered more than the sender’s algorithm."')
sub('Only BBR itself kept up to 35 ms, in its own queue."',
    'Only BBR itself kept up to 35 ms, in its own queue. RED at the same 5 ms fixed only the delay."')

# ---------- Q&A ----------
sub('{c:"Design",q:"How did you configure RED?",s:"Hard limit equal to the other queues, minimum threshold at 1/6 of it and maximum at 1/2, so early random drops start well before the queue is full.",m:"In bytes, with avpkt 1500. RED is known to be sensitive to tuning; I didn’t sweep its parameters, which is a fair limitation.",f:1},',
    '{c:"Design",st:1,sl:5,q:"How did you configure RED?",s:"For the follow-ups, as adaptive RED aimed at fq_codel’s 5 ms: early drops start at 2.5 ms of queue, everything is dropped above 7.5 ms, and the kernel adapts the maximum drop probability between 1 and 50%. The hard limit is the same as the other queues, so only the drop policy differs.",m:"The main study set the thresholds at 1/6 and 1/2 of the buffer, so RED’s target delay grew with the buffer (34 ms at 4× BDP) while fq_codel always aims for 5 ms. That made the delay comparison unfair to RED, so I reran RED in all three experiments with the 5 ms target. Every RED number on the slides comes from those runs."},')
sub('{c:"Results & why",st:1,sl:11,q:"Why didn’t RED help CUBIC?",s:"RED drops from both flows early and at random, but only CUBIC responds to drops. BBR keeps going, so CUBIC stayed around 2% at every buffer size.",m:"RED did cut delay: 48 ms vs 164 on pfifo with four mixed flows. It helps latency, not fairness against a non-responsive sender."},',
    '{c:"Results & why",st:1,sl:11,q:"Why didn’t RED help CUBIC?",s:"RED drops from both flows early and at random, but only CUBIC responds to drops. BBR keeps going, so CUBIC stayed at 2.4–2.5% at every buffer size, and my first RED setting gave the same (2.2–2.5%).",m:"RED did cut delay: 4.8 ms vs 164 on pfifo with four mixed flows at 4× BDP (48 ms with the first setting). It helps latency, not fairness against a sender that ignores drops. With one flow of each it was even worse than the FIFO: CUBIC 5.2% vs 10.9% on the same machine."},')
sub('{c:"Results & why",st:1,sl:12,q:"Why does RED keep the buffer low for Reno and CUBIC but not with BBR?",s:"RED drops early and at random, and Reno and CUBIC back off on those drops, so with only them a deep buffer stayed 12–15% full. BBR likely doesn’t slow down for the drops, so once BBR is in the queue it stayed 23–26% full and BBR kept its lead.",m:"Four BBR flows under RED lost about 48,000 packets per run (6.6% of bytes resent) and still kept the buffer 26% full, close to the 30% on pfifo. One RED setting only (thresholds at 1/6 and 1/2 of the queue), no ECN, second machine."},',
    '{c:"Results & why",st:1,sl:12,q:"Why does RED keep the buffer almost empty?",s:"By design: it aims for 5 ms, about 21 packets, which is only 2.5% of an 834-packet buffer. What I measured is where flows sit against that target: Reno and CUBIC stay under it (0.3–0.4%) and pay in link use, while BBR sits right at it (2.7%), likely because it doesn’t slow down for the early drops.",m:"Reno used 86% of the link there. Four BBR flows lost about 103,000 packets per run (14% resent). My first RED setting tied its thresholds to the buffer and kept it 12–15% full with Reno or CUBIC and 23–26% with BBR. No ECN, second machine."},')
sub('RED gave BBR flows less delay than fq_codel at 0.25× and 1× BDP (5 vs 11 ms, 16 vs 29 ms), but it left CUBIC at 2% of the link.',
    'The first RED setting gave BBR flows less delay than fq_codel at 0.25× and 1× BDP (5 vs 11 ms, 16 vs 29 ms), but it left CUBIC at 2% of the link.')
sub('{c:"Limits",sl:11,q:"Would RED do better with other settings?",s:"Possibly. I tested one setting: early drops starting at 1/6 of the queue, maximum drop probability 0.1 at half the queue, and no ECN. RED is known to need tuning per link, which is part of why CoDel was designed.",m:"The core problem doesn’t depend on the setting, though: RED drops from every flow, but only the loss-based ones slow down, so BBR keeps its lead.",f:1},',
    '{c:"Limits",st:1,sl:14,q:"Would RED do better with other settings?",s:"I tried three. Thresholds tied to the buffer (main study), a 5 ms target like fq_codel (all the slide numbers), and the 5 ms target with the slow queue average the adaptive RED paper recommends. None fixed fairness, and the slow average made things worse.",m:"With the slow average, Reno’s slow start pushed the average above RED’s upper threshold, so RED dropped every arriving packet for seconds at a time, even with an empty queue; Reno used 63–82% of the link even late in each run. The core problem doesn’t depend on the setting: RED drops from every flow, but only loss-based ones slow down. No ECN in any of them."},')
sub('{c:"Results & why",sl:8,q:"Why does CUBIC beat Reno?"',
    '{c:"Results & why",st:1,sl:8,q:"Why does RED make the short path’s advantage bigger?",s:"RED keeps the queue almost empty, so two flows on 20 and 80 ms paths really see 20 and 80 ms, not about 49 and 109 as on a full FIFO. RED also drops every packet with the same probability, so a loss-based flow’s rate likely scales with one over its RTT, and a 4× RTT gap becomes about a 4× throughput gap.",m:"A model with each flow’s rate proportional to one over its measured RTT predicts a Jain index of 0.74 for two Reno flows; I measured 0.75. Four Reno flows: 0.73 under RED vs 0.88 on pfifo, same machine. BBR doesn’t follow the model (0.99), since it doesn’t react to the drops."},\n'
    '{c:"Results & why",st:1,sl:8,q:"Why does RED cost Reno throughput?",s:"RED starts dropping at 2.5 ms of queue and drops everything above 7.5 ms, so for Reno it acts like a buffer of only 0.06–0.19 BDP. After Reno halves there’s no backlog to keep the link busy. The same sawtooth model that predicted my 0.25× BDP result predicts 79–86%, and I measured 83–87%.",m:"CUBIC only cuts to 70%, so it lost 3–6%. Under fq_codel, with the same 5 ms target, Reno kept 94–98% (95% vs 86% on the same machine at 4× BDP), likely because CoDel only starts dropping after 100 ms above target, so short bursts get through."},\n'
    '{c:"Results & why",sl:8,q:"Why does CUBIC beat Reno?"')
sub('pfifo 1.4 / 1.8 / 58.9%. RED 2.2 / 2.3 / 2.5%.', 'pfifo 1.4 / 1.8 / 58.9%. RED* 2.4 / 2.5 / 2.4% (first RED setting 2.2 / 2.3 / 2.5%).')
sub('RED: 12, 15, 26, 23%. fq_codel: 0.9, 0.9, 7, 7%.', 'RED* (5 ms target): 0.3, 0.4, 2.7, 2.3%, low by design. fq_codel: 0.9, 0.9, 7, 7%.')
sub('s:"pfifo 164 ms, RED 48 ms, fq_codel 3 ms', 's:"pfifo 164 ms, RED* 4.8 ms (48 ms with the first setting), fq_codel 3 ms')
sub('16 configs captured.",m:""}', '16 configs captured. Follow-ups on a second machine: 482 more runs, 277 of them RED.",m:""}')
sub('Before trusting them, I re-ran ten of the original settings there, and they matched the VM within the confidence intervals apart from five small gaps.",',
    'Before trusting them, I re-ran ten of the original settings there, and eight more with the RED runs, and they matched the VM within the confidence intervals apart from small gaps.",')

open(OUT, 'w', encoding='utf8').write(s)
print('ok', len(s))

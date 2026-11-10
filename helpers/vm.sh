# VM shortcuts for the project. Loaded from ~/.bashrc (see the guide's one-time setup).

# Newest trial-1 folder of a configuration. Optional 3rd argument picks special runs
# (staggered, udpdelay); without it they are skipped.   trial s1 n1-reno
trial() {
    ls -d ~/tcp-congestion/results/$1/*/$2/trial_1 2>/dev/null |
        { if [ -n "$3" ]; then grep -- "$3"; else grep -v -e staggered -e udpdelay; fi; } | tail -1
}

# Last sample of a qdisc.txt (the final drop counters).   lastblock "$(trial s2 udp100-cubic-pfifo udpdelay)/qdisc.txt"
lastblock() {
    awk '/^T /{b=""} {b=b $0 "\n"} END{printf "%s", b}' "$1"
}

# Largest bottleneck backlog seen during a trial.   maxbacklog "$(trial s3 n4-b4-rtt50-cubic+bbr-pfifo)/qdisc.txt"
maxbacklog() {
    (cd ~/tcp-congestion && python3 -c "import sys; from pathlib import Path; from analysis.parse import parse_qdisc; r = parse_qdisc(Path(sys.argv[1]), 0); t, b, d, _ = max(r, key=lambda x: x[1]); print(f'largest backlog: {b} packets (cumulative drops {d})')" "$1")
}

# Count completed main trials of a scenario (staggered and late-UDP runs excluded).   done_count s1
done_count() {
    find ~/tcp-congestion/results/$1 \( -path '*staggered*' -o -path '*udpdelay*' \) -prune \
        -o -name done -print | wc -l
}

# UDP jitter and loss from an iperf3 client result.   udpq "$(trial s2 udp100-cubic-pfifo)/h4_udp.json"
udpq() {
    python3 -c 'import json, sys
e = json.load(open(sys.argv[1]))["end"]
s = next(e[k] for k in ("sum_received", "sum", "sum_sent") if k in e and "lost_percent" in e[k])
print("jitter %.2f ms, loss %.1f%%" % (s["jitter_ms"], s["lost_percent"]))' "$1"
}

# Mean probe RTT (idle, loaded p50/p95, queueing delay) per configuration, after analysis.parse.
#   probertt s3 n4-b4-
probertt() {
    (cd ~/tcp-congestion && python3 -c 'import sys, pandas as pd
t = pd.read_csv(f"data/{sys.argv[1]}_trials.csv")
t = t[t.config.str.startswith(sys.argv[2]) & ~t.special]
cols = ["idle_rtt_ms", "probe_rtt_p50", "probe_rtt_p95", "queue_delay_ms"]
print(t.groupby("config")[cols].mean().round(1).to_string())' "$1" "$2")
}

# Rerun every configuration that "analysis.metrics <scenario> --check" flags, with 8 trials,
# then re-parse so the next --check sees the new trials.
#   rerun_flagged s1
rerun_flagged() {
    (cd ~/tcp-congestion || return
     python3 -m analysis.parse "$1" > /dev/null
     ids=$(python3 -m analysis.metrics "$1" --flagged)
     [ -n "$ids" ] || { echo "nothing flagged"; return; }
     args=()
     for id in $ids; do args+=(--only "$id"); done
     echo "rerunning: $ids"
     sudo python3 -u run.py experiments/$1_*.yaml "${args[@]}" --trials "${2:-8}"
     python3 -m analysis.parse "$1")
}

# Mac shortcuts for the project. Loaded from ~/.zshrc (see the guide's one-time setup).
setopt interactive_comments        # lets pasted commands carry "# ..." comments
export TCP=~/Desktop/SJSU/cmpe-206-network/project/tcp-congestion

# Send code to the VM (code only, so nothing on the VM is overwritten).
tcp-push() {
    (cd "$TCP" && rsync -avR .gitignore run.py demo.py topo traffic analysis experiments helpers \
        tcpvm:~/tcp-congestion/)
}

# Bring evidence, results, parsed data and figures back from the VM. Never deletes anything here.
tcp-pull() {
    rsync -av tcpvm:~/tcp-congestion/{evidence,results,data,figures,notebook.md} "$TCP/"
}

# File the newest screenshot on the Desktop as evidence:  shot step5-s1/E5.1_s1-reno-inflight.png
shot() {
    local src
    src=$(ls -t ~/Desktop/Screenshot*.png 2>/dev/null | head -1)
    [ -n "$src" ] || { echo "no screenshot on the Desktop"; return 1; }
    mkdir -p "$TCP/evidence/$(dirname "$1")"
    mv "$src" "$TCP/evidence/$1" && echo "saved evidence/$1"
}

# Newest trial-1 folder of a configuration. Optional 3rd argument picks special runs
# (staggered, udpdelay); without it they are skipped.
trial() {
    ls -d "$TCP"/results/$1/*/$2/trial_1 2>/dev/null |
        { if [ -n "$3" ]; then grep -- "$3"; else grep -v -e staggered -e udpdelay; fi; } | tail -1
}

# Open a capture in Wireshark:  cap s1 n1-reno sender_h1.pcap   |   cap s2 udp100-cubic-pfifo bottleneck.pcap udpdelay
cap() {
    local dir
    dir=$(trial "$1" "$2" "$4")
    [ -n "$dir" ] || { echo "no trial found for $1 $2 $4 - run tcp-pull first?"; return 1; }
    open -a Wireshark "$dir/$3"
}

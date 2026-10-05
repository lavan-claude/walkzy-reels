#!/bin/sh
# Baut aus reels/DATUM-c.json das fertige Reel mit Musik: reels/DATUM-c_musik.mp4
# Aufruf: tools/build_reel.sh reels/2026-10-06-c.json [wendepunkt_sek]
set -e
J="$1"; B="${J%.json}"; T="${2:-}"
python3 tools/make_reel.py "$J" >/dev/null
D=$(python3 -c "import json,sys;print(json.load(open('$J'))['duration'])")
[ -z "$T" ] && T=$(python3 -c "import json;d=json.load(open('$J'));s=d['scenes'];print(s[min(3,len(s)-1)]['t0'])")
W=$(mktemp --suffix=.wav)
python3 tools/make_music.py "$W" "$D" "$T" "$T"
FO=$(python3 -c "print(max(0,$D-1.5))")
ffmpeg -v error -y -i "$B.mp4" -i "$W" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -af "afade=t=out:st=$FO:d=1.5" -shortest "${B}_musik.mp4"
rm -f "$W"; echo "fertig: ${B}_musik.mp4"

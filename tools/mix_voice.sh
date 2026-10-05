#!/bin/sh
# Legt eine Sprachaufnahme (mp3/wav/m4a) ueber das Reel; Musik wird leiser, solange gesprochen wird.
# Aufruf: tools/mix_voice.sh reel_ohne_ton.mp4 musik.wav stimme.mp3 ausgabe.mp4
ffmpeg -v error -y -i "$1" -i "$2" -i "$3" -filter_complex "[2:a]loudnorm=I=-16:TP=-1.5,asplit=2[v1][v2];[1:a]volume=0.55[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];[md][v2]amix=inputs=2:duration=first:normalize=0,afade=t=out:st=18.5:d=1.5[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest "$4"

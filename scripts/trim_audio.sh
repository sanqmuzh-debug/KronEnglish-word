#!/bin/bash
# 剪掉一段 mp3 开头和结尾的空白（Fish 每段前面有约 0.18 秒静音，点积木会觉得慢半拍）。
# 用法：ls demo/audio-fish/*.mp3 | xargs -P 8 -n 1 scripts/trim_audio.sh
f="$1"; t="${f%.mp3}.tmp.mp3"
ffmpeg -v error -y -i "$f" -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse" -ac 1 -codec:a libmp3lame -b:a 64k "$t" && mv "$t" "$f"

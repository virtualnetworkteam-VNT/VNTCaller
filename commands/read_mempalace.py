
import os
mp = open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md").read()
# Search for Play Console, Google Play, VNTCaller app mentions
keywords = ["play console","google play","developer","vntcaller","package","signing","keystore","upload","apk","aab","account","kraheelw"]
lines = mp.split("\n")
relevant = []
for i,line in enumerate(lines):
    if any(k in line.lower() for k in keywords):
        start = max(0,i-1)
        end = min(len(lines),i+3)
        relevant.extend(lines[start:end])
        relevant.append("---")
print("\n".join(relevant[-100:]))

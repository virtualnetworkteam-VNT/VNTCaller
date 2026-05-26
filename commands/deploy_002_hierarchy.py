
import subprocess, time

h = open("/home/k/vnt-web/vnt_hierarchy.html").read()

fixes = [
    ("Avi","Julian","julian","Project Manager",7780),
    ("Luc","Maya","maya","HR Manager",7778),
    ("Dina","Ethan","ethan","Medical Expert",7781),
    ("Ben","Ava","ava","File Secretary",7779),
    ("Lee","Lee","lee","Marketing Mgr",7782),
    ("Amr","Amr","amr","Legal Advisor",7783),
]

for old,new,nid,role,port in fixes:
    h = h.replace(
        f'class="node planned"><div class="node-name">{old}</div>',
        f'class="node active" id="node-{nid}"><div class="node-name">{new}</div>'
    )
    h = h.replace(
        f'badge-planned">Planned</span></div>\n    <div class="node',
        f'badge-active" id="badge-{nid}-agent">Active</span></div>\n    <div class="node',
        1
    )

# Add Nova card and live JS
nova = '<div style="margin:5px;border:2px solid #00ff88;padding:10px;border-radius:8px;display:inline-block;background:#1a1a2e"><b style="color:#fff">Nova</b><br><small style="color:#888">Civil Architect :7784</small><br><span id="badge-nova-agent" style="background:#00ff88;color:#000;padding:2px 6px;border-radius:4px;font-size:11px">Active</span></div>'

live_js = '<script>async function liveStatus(){try{const r=await fetch("http://192.168.10.96:7777/status/all");const d=await r.json();const c={green:"#00ff88",orange:"#ff8800",red:"#ff4444"};Object.entries(d).forEach(([s,i])=>{const b=document.getElementById("badge-"+s.replace("-agent","")+"-agent");if(b){b.style.background=c[i.color]||"#888";b.style.color="black";b.textContent=i.status;}});}catch(e){}}setInterval(liveStatus,15000);liveStatus();</script>'

if "liveStatus" not in h:
    h = h.replace("</body>", nova + live_js + "</body>")

open("/home/k/vnt-web/vnt_hierarchy.html","w").write(h)
subprocess.run(["sudo","systemctl","restart","vnt-webserver"],capture_output=True)
print("Hierarchy updated - all agents active")

# Update Zeus to monitor all new agents
zm = open("/home/k/zeus-monitor.py").read()
for ag in ["julian-agent","maya-agent","ethan-agent","ava-agent","lee-agent","amr-agent","nova-agent"]:
    if ag not in zm:
        zm = zm.replace('"ethan-agent"', f'"ethan-agent","{ag}"')
open("/home/k/zeus-monitor.py","w").write(zm)
subprocess.run(["sudo","systemctl","restart","zeus-monitor"],capture_output=True)
print("Zeus monitoring all agents")

with open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md","a") as f:
    f.write(f"\n### Hierarchy & Zeus Updated [{__import__('time').strftime('%Y-%m-%d %H:%M')}]\nAll agents shown on hierarchy page with live status\n")

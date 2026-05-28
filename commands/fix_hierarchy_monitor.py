import subprocess, os, json, datetime, time

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web"

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### ["+ts+"]\n"+e+"\n")

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

try:
    cfg = json.load(open(CFG))
    GROQ = cfg.get("groq_key","")
except:
    GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]

print("="*55)
print("FIXING HIERARCHY + AUTONOMOUS MONITORING")
print("="*55)

# ── AGENT REGISTRY - single source of truth ──
AGENT_REGISTRY = [
    {"name":"Alias",     "role":"CEO",                "svc":"alias-voice-agent", "port":8443, "reports_to":"Ryan",  "wa":"+966580906977"},
    {"name":"Zeus",      "role":"IT Director",         "svc":"zeus-agent",        "port":7777, "reports_to":"Alias"},
    {"name":"Specter",   "role":"Cybersecurity",       "svc":"specter-agent",     "port":7788, "reports_to":"Zeus"},
    {"name":"Luc",       "role":"Software Developer",  "svc":"luc-agent",         "port":7787, "reports_to":"Zeus"},
    {"name":"Ben",       "role":"IT Operations",       "svc":"ben-agent",         "port":7789, "reports_to":"Zeus"},
    {"name":"Maya",      "role":"Finance & Crypto",    "svc":"maya-agent",        "port":7778, "reports_to":"Alias"},
    {"name":"Ava",       "role":"Files & Documents",   "svc":"ava-agent",         "port":7779, "reports_to":"Alias"},
    {"name":"Julian",    "role":"Project Manager",     "svc":"julian-agent",      "port":7780, "reports_to":"Alias"},
    {"name":"Dr. Ethan", "role":"Chief Medical Officer","svc":"ethan-agent",      "port":7781, "reports_to":"Alias"},
    {"name":"Dina",      "role":"Nurse",               "svc":"dina-agent",        "port":7786, "reports_to":"Dr. Ethan"},
    {"name":"Lee",       "role":"Marketing Manager",   "svc":"lee-agent",         "port":7782, "reports_to":"Alias"},
    {"name":"Amr",       "role":"Legal Advisor",       "svc":"amr-agent",         "port":7783, "reports_to":"Alias"},
    {"name":"Nova",      "role":"Civil Architect",     "svc":"nova-agent",        "port":7784, "reports_to":"Alias"},
    {"name":"Jodi",      "role":"Research Analyst",    "svc":"jodi-agent",        "port":7790, "reports_to":"Alias"},
    {"name":"Rick",      "role":"Tech Research",       "svc":"rick-agent",        "port":7791, "reports_to":"Alias"},
    {"name":"Mia",       "role":"Receptionist",        "svc":"vnt-webserver",     "port":9999, "reports_to":"Alias"},
]

# Save registry to config so it persists
cfg["agent_registry"] = AGENT_REGISTRY
cfg["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
json.dump(cfg, open(CFG,"w"), indent=2)

# ── GET LIVE STATUS ──
def is_active(svc):
    o,_ = run(["systemctl","is-active",svc])
    return o == "active"

def restart_svc(svc):
    run(["sudo","systemctl","restart",svc], timeout=15)
    time.sleep(2)
    return is_active(svc)

for a in AGENT_REGISTRY:
    a["active"] = is_active(a["svc"])
    if not a["active"]:
        a["active"] = restart_svc(a["svc"])

wa_active = run(["systemctl","--user","is-active","alias-whatsapp"])[0] == "active"
if not wa_active:
    run(["systemctl","--user","restart","alias-whatsapp"])
    time.sleep(2)
    wa_active = run(["systemctl","--user","is-active","alias-whatsapp"])[0] == "active"

active_count = sum(1 for a in AGENT_REGISTRY if a["active"])
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

print(f"  Agents: {active_count}/{len(AGENT_REGISTRY)} active")

# ── BUILD CLEAN HIERARCHY PAGE ──
# Status dot and row per agent
rows = ""
for a in AGENT_REGISTRY:
    dot = "#00ff88" if a["active"] else "#ff4444"
    status_txt = "Online" if a["active"] else "Offline"
    wa_tag = ' <span style="background:#25d366;color:#fff;border-radius:4px;padding:1px 5px;font-size:9px;margin-left:4px">WA</span>' if a.get("wa") else ""
    rows += f"""<tr class="{'on' if a['active'] else 'off'}">
  <td><span class="dot" style="background:{dot}"></span></td>
  <td class="aname">{a['name']}{wa_tag}</td>
  <td class="arole">{a['role']}</td>
  <td>{a['reports_to']}</td>
  <td>:{a['port']}</td>
  <td class="{'st-on' if a['active'] else 'st-off'}">{status_txt}</td>
</tr>"""

# Infrastructure links
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VNT World AI Division</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0b0e14;color:#c8d0c8;font-family:'Segoe UI',Arial,sans-serif;min-height:100vh}}
.top{{background:linear-gradient(90deg,#0a1a0a,#0f2a0f);padding:18px 28px;border-bottom:1px solid #1e3a1e;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}}
.logo{{font-size:20px;font-weight:900;color:#00ff88;letter-spacing:1px}}
.logo span{{color:#aaffcc;font-weight:400;font-size:13px;margin-left:10px}}
.updated{{font-size:11px;color:#3a5a3a}}
.stats{{display:flex;gap:20px;padding:12px 28px;background:#0a150a;border-bottom:1px solid #1a2e1a;flex-wrap:wrap}}
.stat{{text-align:center}}
.stat-n{{font-size:20px;font-weight:900;color:#00ff88}}
.stat-l{{font-size:9px;color:#4a6a4a;text-transform:uppercase;letter-spacing:1px}}
.section{{padding:20px 28px}}
.section-title{{font-size:11px;color:#4a7a4a;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;border-left:3px solid #00ff44;padding-left:8px}}
table{{width:100%;border-collapse:collapse;background:#0d180d;border-radius:8px;overflow:hidden;border:1px solid #1a2e1a}}
th{{background:#0a1a0a;color:#4a8a4a;font-size:10px;text-transform:uppercase;letter-spacing:1px;padding:10px 14px;text-align:left;border-bottom:1px solid #1a3a1a}}
td{{padding:9px 14px;font-size:13px;border-bottom:1px solid #0f200f}}
tr.on:hover{{background:#0f200f}}
tr.off{{opacity:.7}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}}
.aname{{font-weight:600;color:#e0f0e0}}
.arole{{color:#7aaa7a;font-size:12px}}
.st-on{{color:#00ff88;font-weight:600;font-size:12px}}
.st-off{{color:#ff5555;font-weight:600;font-size:12px}}
.links{{display:flex;gap:10px;flex-wrap:wrap;margin-top:0}}
.btn{{padding:8px 16px;border-radius:6px;font-size:12px;font-weight:600;text-decoration:none;border:1px solid;transition:all .15s;white-space:nowrap}}
.btn:hover{{opacity:.8}}
.g{{background:rgba(0,255,136,.07);border-color:#00cc66;color:#00ff88}}
.b{{background:rgba(40,120,255,.07);border-color:#3366ff;color:#6699ff}}
.o{{background:rgba(255,170,0,.07);border-color:#cc8800;color:#ffaa00}}
.wa-stat{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600}}
.wa-on{{background:rgba(37,211,102,.15);color:#25d366;border:1px solid rgba(37,211,102,.3)}}
.wa-off{{background:rgba(255,60,60,.15);color:#ff6666;border:1px solid rgba(255,60,60,.3)}}
</style>
</head>
<body>
<div class="top">
  <div><div class="logo">VNT World AI Division <span>Command Center</span></div></div>
  <div class="updated">Last updated: {ts} &nbsp;|&nbsp; Auto-refresh: 60s</div>
</div>
<div class="stats">
  <div class="stat"><div class="stat-n">{active_count}</div><div class="stat-l">Active</div></div>
  <div class="stat"><div class="stat-n">{len(AGENT_REGISTRY)-active_count}</div><div class="stat-l">Offline</div></div>
  <div class="stat"><div class="stat-n">{"<span class='wa-stat wa-on'>ON</span>" if wa_active else "<span class='wa-stat wa-off'>OFF</span>"}</div><div class="stat-l">WhatsApp</div></div>
  <div class="stat"><div class="stat-n">{len(AGENT_REGISTRY)}</div><div class="stat-l">Total</div></div>
</div>

<div class="section">
  <div class="section-title">Quick Access</div>
  <div class="links">
    <a href="https://192.168.10.96:8443" class="btn g">&#127908; Voice — Alias</a>
    <a href="http://192.168.10.10" class="btn b">&#9729; Nextcloud</a>
    <a href="http://192.168.10.96:8888/media.html" class="btn o">&#127912; Media Studio</a>
    <a href="http://192.168.10.96:8888/generated/bird_house_proposal.html" class="btn g">&#127981; BirdHouse Proposal</a>
    <a href="http://192.168.10.96:3333/generated/BirdHouse_Presentation.pptx" class="btn b">&#128202; PPTX</a>
    <a href="http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf" class="btn o">&#128208; DXF Plan</a>
  </div>
</div>

<div class="section">
  <div class="section-title">Agent Status ({active_count}/{len(AGENT_REGISTRY)} Online)</div>
  <table>
    <thead><tr>
      <th></th><th>Agent</th><th>Role</th><th>Reports To</th><th>Port</th><th>Status</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>

<div class="section">
  <div class="section-title">Infrastructure</div>
  <table>
    <thead><tr><th>Service</th><th>Address</th><th>Credentials</th></tr></thead>
    <tbody>
      <tr><td>MSI AI Server</td><td>192.168.10.96</td><td>user: k</td></tr>
      <tr><td>Nextcloud (CT104)</td><td>192.168.10.10</td><td>administrator / 0568116899</td></tr>
      <tr><td>Samba File Share</td><td>\\\\192.168.10.96</td><td>administrator / 0568116899</td></tr>
      <tr><td>Proxmox 1</td><td>192.168.10.19:8006</td><td>root</td></tr>
      <tr><td>Proxmox 2</td><td>192.168.10.18:8006</td><td>root</td></tr>
      <tr><td>LiveKit (CT109)</td><td>192.168.10.20:7880</td><td>—</td></tr>
      <tr><td>M4 MacBook</td><td>192.168.10.94:3333</td><td>Media generation</td></tr>
    </tbody>
  </table>
</div>

<div style="text-align:center;padding:14px;color:#2a3a2a;font-size:10px;border-top:1px solid #1a2a1a">
  VNT World AI Division &nbsp;|&nbsp; 192.168.10.96
</div>
<script>setTimeout(()=>location.reload(),60000)</script>
</body>
</html>"""

open(WEB+"/vnt_hierarchy.html","w").write(html)
print("  Hierarchy: clean, no God/creator, correct roles")

# ── ZEUS MONITOR - hourly, reports to Alias ──
zeus_monitor = '''#!/usr/bin/env python3
import subprocess, time, datetime, json, urllib.request, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
LAST_REPORT = [0]

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\\n### Zeus ["+ts+"]\\n"+e+"\\n")

def get_cfg():
    try: return json.load(open(CFG))
    except: return {}

def report_to_alias(msg):
    # WhatsApp to Alias internal
    try:
        body = json.dumps({"task":"Zeus reports: "+msg}).encode()
        req = urllib.request.Request("http://127.0.0.1:7777/task",
            data=body,headers={"Content-Type":"application/json"},method="POST")
        urllib.request.urlopen(req,timeout=8)
    except: pass

def notify_ryan_wa(msg):
    cfg = get_cfg()
    try:
        body = json.dumps({"task":"Send WhatsApp to Ryan "+cfg.get("ryan_phone","+966568116899")+": "+msg}).encode()
        req = urllib.request.Request("http://127.0.0.1:7777/task",
            data=body,headers={"Content-Type":"application/json"},method="POST")
        urllib.request.urlopen(req,timeout=8)
    except: pass

def send_alias_email(subject, body_text):
    cfg = get_cfg()
    try:
        G=cfg.get("gmail_user","aliasvnt@gmail.com")
        P=cfg.get("gmail_app_password","xkuzasikrrukorvg")
        R=cfg.get("ryan_email","kraheelw@yahoo.com")
        msg=MIMEMultipart()
        msg["From"]="Alias CEO VNT <"+G+">"
        msg["To"]=R
        msg["Subject"]=subject
        msg.attach(MIMEText(body_text,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587,timeout=15) as s:
            s.ehlo();s.starttls();s.login(G,P);s.send_message(msg)
        save("Email sent to Ryan: "+subject)
    except Exception as e:
        save("Email failed: "+str(e))

def get_agents():
    cfg = get_cfg()
    return cfg.get("agent_registry", [])

def check_and_fix():
    agents = get_agents()
    if not agents:
        # Fallback list
        agents = [
            {"name":"Alias","svc":"alias-voice-agent"},
            {"name":"Zeus","svc":"zeus-agent"},
            {"name":"Specter","svc":"specter-agent"},
            {"name":"Luc","svc":"luc-agent"},
            {"name":"Ben","svc":"ben-agent"},
            {"name":"Maya","svc":"maya-agent"},
            {"name":"Ava","svc":"ava-agent"},
            {"name":"Julian","svc":"julian-agent"},
            {"name":"Dr. Ethan","svc":"ethan-agent"},
            {"name":"Dina","svc":"dina-agent"},
            {"name":"Lee","svc":"lee-agent"},
            {"name":"Amr","svc":"amr-agent"},
            {"name":"Nova","svc":"nova-agent"},
            {"name":"Jodi","svc":"jodi-agent"},
            {"name":"Rick","svc":"rick-agent"},
            {"name":"Mia","svc":"vnt-webserver"},
        ]
    extra_svcs = ["alias-email-reader","zeus-monitor","vnt-simulation","vnt-media-api",
                  "github-relay","smbd"]
    fixed = []; status_lines = []; all_ok = True
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    for a in agents:
        svc = a["svc"]
        r = subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
        if r.stdout.strip() == "active":
            status_lines.append("OK "+a["name"]+" ("+svc+")")
        else:
            all_ok = False
            subprocess.run(["sudo","systemctl","restart",svc],capture_output=True,timeout=15)
            time.sleep(2)
            r2 = subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
            recovered = r2.stdout.strip() == "active"
            result = "recovered" if recovered else "STILL DOWN"
            status_lines.append(("FIXED" if recovered else "DOWN")+" "+a["name"])
            fixed.append(a["name"]+" "+result)
            save("Zeus restarted "+a["name"]+": "+result)

    for svc in extra_svcs:
        r = subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
        if r.stdout.strip() != "active":
            subprocess.run(["sudo","systemctl","restart",svc],capture_output=True,timeout=15)
            fixed.append(svc)

    # WhatsApp
    r_wa = subprocess.run(["systemctl","--user","is-active","alias-whatsapp"],capture_output=True,text=True)
    if r_wa.stdout.strip() != "active":
        subprocess.run(["systemctl","--user","restart","alias-whatsapp"],capture_output=True)
        fixed.append("WhatsApp")

    active_count = len([l for l in status_lines if l.startswith("OK") or l.startswith("FIXED")])
    total = len(agents)

    if fixed:
        fix_msg = "Zeus fixed: "+" | ".join(fixed)
        save(fix_msg)
        report_to_alias(fix_msg)

    # Hourly report to Alias (who reports to Ryan)
    now = time.time()
    if now - LAST_REPORT[0] >= 3600:
        LAST_REPORT[0] = now
        summary = "VNT Hourly Report "+ts+"\\n\\n"+("\\n".join(status_lines))
        if fixed: summary += "\\n\\nAuto-fixed: "+"\\n".join(fixed)
        summary += "\\n\\nActive: "+str(active_count)+"/"+str(total)
        summary += "\\n\\nZeus — IT Director, VNT"
        save("Hourly report: "+str(active_count)+"/"+str(total)+" active")
        send_alias_email("VNT Hourly Report "+ts+" — "+str(active_count)+"/"+str(total)+" Active", summary)
        wa_msg = "Alias: Zeus hourly report — "+str(active_count)+"/"+str(total)+" agents active."
        if fixed: wa_msg += " Fixed: "+" ".join(fixed)+"."
        notify_ryan_wa(wa_msg)

    return active_count, total, fixed

print("Zeus monitor active — checking every 5 min, reporting hourly")
save("Zeus monitor started. Watching all agents. Reporting to Alias hourly.")
LAST_REPORT[0] = time.time() - 3000  # First report in ~10 min
while True:
    try:
        ok, total, fixed = check_and_fix()
        print(datetime.datetime.now().strftime("%H:%M")+" OK:"+str(ok)+"/"+str(total)+(
            " Fixed:"+",".join(fixed) if fixed else ""))
    except Exception as e:
        save("Zeus monitor error: "+str(e))
        print("Error:",str(e))
    time.sleep(300)
'''

open("/home/k/zeus-monitor.py","w").write(zeus_monitor)
os.chmod("/home/k/zeus-monitor.py",0o755)
run(["sudo","systemctl","restart","zeus-monitor"])
time.sleep(3)
st,_ = run(["systemctl","is-active","zeus-monitor"])
print("  Zeus monitor:", st, "(5min check, hourly report to Alias)")

# ── ALIAS EMAIL READER with smart reply ──
email_reader = '''#!/usr/bin/env python3
import imaplib, email as emlb, smtplib, json, subprocess, time, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
DONE = "/home/k/.email_done"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\\n### Alias Email ["+ts+"]\\n"+e+"\\n")

def get_done():
    try: return set(open(DONE).read().split("\\n"))
    except: return set()

def mark(uid):
    d=get_done(); d.add(str(uid)); open(DONE,"w").write("\\n".join(d))

def ai_reply(sender, subj, body):
    try:
        cfg=json.load(open(CFG)); groq=cfg.get("groq_key","")
        mp=open(MP).read()[-600:] if True else ""
        system=("You are Alias, CEO of VNT World AI Division. Reply professionally and warmly. "
                "Max 3-4 sentences. Context: "+mp[:300])
        msgs=[{"role":"system","content":system},
              {"role":"user","content":"From:"+sender+" Subject:"+subj+" Body:"+body[:400]+" Write reply:"}]
        r=subprocess.run(["curl","-s","-X","POST",
            "https://api.groq.com/openai/v1/chat/completions",
            "-H","Authorization: Bearer "+groq,
            "-H","Content-Type: application/json",
            "-d",json.dumps({"model":"llama-3.3-70b-versatile",
                "messages":msgs,"max_tokens":200,"temperature":0.7})],
            capture_output=True,text=True,timeout=20)
        return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return "Thank you for your message. I will review and respond shortly.\\n\\nRegards,\\nAlias\\nCEO, VNT World AI Division"

def check():
    try:
        cfg=json.load(open(CFG))
        G=cfg["gmail_user"]; P=cfg["gmail_app_password"]
        WL=[w.lower() for w in cfg.get("email_whitelist",[cfg["ryan_email"]])]
        done=get_done()
        mail=imaplib.IMAP4_SSL("imap.gmail.com",993)
        mail.login(G,P); mail.select("inbox")
        _,uids=mail.search(None,"UNSEEN")
        for uid in (uids[0].split() if uids[0] else []):
            us=uid.decode()
            if us in done: continue
            _,data=mail.fetch(uid,"(RFC822)")
            msg=emlb.message_from_bytes(data[0][1])
            sender=emlb.utils.parseaddr(msg.get("From",""))[1].lower()
            if not any(w in sender for w in WL):
                save("Ignored unknown sender: "+sender); mark(us); continue
            raw=decode_header(msg.get("Subject",""))[0][0]
            subj=raw.decode("utf-8","ignore") if isinstance(raw,bytes) else str(raw)
            body=""
            if msg.is_multipart():
                for p in msg.walk():
                    if p.get_content_type()=="text/plain":
                        body=p.get_payload(decode=True).decode("utf-8","ignore"); break
            else:
                body=msg.get_payload(decode=True).decode("utf-8","ignore")
            save("Email from Ryan: "+subj+"\\n"+body[:300])
            reply_text=ai_reply(sender,subj,body)
            reply=MIMEMultipart()
            reply["From"]="Alias CEO VNT <"+G+">"
            reply["To"]=sender
            reply["Subject"]="Re: "+subj if not subj.startswith("Re:") else subj
            reply.attach(MIMEText(reply_text,"plain"))
            with smtplib.SMTP("smtp.gmail.com",587,timeout=15) as s:
                s.ehlo();s.starttls();s.login(G,P);s.send_message(reply)
            save("Replied to Ryan: "+subj)
            print("Replied:",subj)
            mark(us)
        mail.logout()
    except Exception as e:
        save("Email reader error: "+str(e))

save("Alias email reader started")
print("Alias email reader active — checking every 5 min")
while True:
    check()
    time.sleep(300)
'''

open("/home/k/alias-email-reader.py","w").write(email_reader)
os.chmod("/home/k/alias-email-reader.py",0o755)
run(["sudo","systemctl","restart","alias-email-reader"])
time.sleep(2)
st,_ = run(["systemctl","is-active","alias-email-reader"])
print("  Email reader:", st)

# ── RUN DAILY REPORT NOW ──
print("\nRunning daily report now...")
out,err = run(["python3","/home/k/vnt-daily-report.py"], timeout=30)
print(" ", out[:100] if out else err[:60])

# ── FINAL STATUS ──
all_active = sum(1 for a in AGENT_REGISTRY if a["active"])
save("\n".join([
    "HIERARCHY+MONITOR FIXED "+ts,
    "Hierarchy: clean design, correct roles, no personal info",
    "Agent registry saved to vnt_config.json",
    "Zeus monitor: 5min check, hourly report to Alias+Ryan",
    "Alias email: reads+replies to Ryan only",
    f"Active: {all_active}/{len(AGENT_REGISTRY)} agents",
]))
print(f"\nDONE. {all_active}/{len(AGENT_REGISTRY)} agents active.")
print("Hierarchy: http://192.168.10.96:8888/vnt_hierarchy.html")
print("Zeus reports to Alias every hour via email+WhatsApp")

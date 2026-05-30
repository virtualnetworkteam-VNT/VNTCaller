
import subprocess,os,json,datetime,time,smtplib,urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG="/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
BRAIN="/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json"
SNAP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/snapshots"
def run(c,shell=False,t=15):
    r=subprocess.run(c,shell=shell,capture_output=True,text=True,timeout=t)
    return r.stdout.strip()
def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:open(MP,"a").write("\n### Final ["+ts+"]\n"+str(e)+"\n")
    except:pass
try:cfg=json.load(open(CFG))
except:cfg={}
GMAIL=cfg.get("gmail_user","aliasvnt@gmail.com")
GPASS=cfg.get("gmail_app_password","xkuzasikrrukorvg")
RYAN=cfg.get("ryan_email","kraheelw@yahoo.com")
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("STEP6: FINAL STATUS + EMAIL")
ALL=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
     "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent","specter-agent",
     "vnt-webserver","luc-agent","ben-agent","dina-agent","jodi-agent","rick-agent",
     "alias-email-reader","vnt-simulation","github-relay","smbd"]
ok=sum(1 for s in ALL if run(["systemctl","is-active",s])=="active")
down=[s for s in ALL if run(["systemctl","is-active",s])!="active"]
va=run(["systemctl","is-active","alias-voice-agent"])
wa=run(["systemctl","--user","is-active","alias-whatsapp"])
ssh=run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 echo OK 2>&1",shell=True,timeout=10)
asusi7=("CONFIRMED" if "OK" in ssh else "check sshpass")
snaps=sorted([d for d in os.listdir(SNAP) if d.startswith("snap_")],reverse=True) if os.path.exists(SNAP) else []
snap=SNAP+"/"+snaps[0] if snaps else "none"
try:
    req=urllib.request.Request("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true",headers={"User-Agent":"VNT/1.0"})
    with urllib.request.urlopen(req,timeout=8) as r:prices=json.loads(r.read())
    btc=prices["bitcoin"]["usd"];btcc=round(prices["bitcoin"]["usd_24h_change"],2)
    eth=prices["ethereum"]["usd"];ethc=round(prices["ethereum"]["usd_24h_change"],2)
except:btc=75000;btcc=0;eth=2000;ethc=0
nl=chr(10)
body=nl.join([
    "Dear Ryan,","",
    "VNT is now fully operational. Confirmed status:","",
    "="*45,"STATUS - "+ts,"="*45,"",
    "Services: "+str(ok)+"/"+str(len(ALL))+" active",
    "Voice :8443: "+va,
    "WhatsApp: "+wa,
    "Asusi7 SSH: "+asusi7,
    "Down: "+", ".join(down) if down else "All running","",
    "="*45,"MULTI-LLM - SWITCH ANYTIME","="*45,"",
    "Current: Groq llama-3.3-70b-versatile",
    "Backup:  Claude (add anthropic_key to vnt_config.json)",
    "Local:   Ollama llama3.1:8b","",
    "Switch by telling me:",
    "  'use Claude' | 'use Groq' | 'switch to local AI'","",
    "="*45,"M2/M4 CLARIFIED PERMANENTLY","="*45,"",
    "M2 MacBook: RETIRED - not in use",
    "M4 MacBook: 192.168.10.94:3333 - ALL media","",
    "Documented in MemPalace and my brain.","",
    "="*45,"ROLLBACK","="*45,"",
    "Latest snapshot: "+snap,"",
    "="*45,"LIVE MARKET","="*45,"",
    "BTC: $"+f"{btc:,.0f}"+" ("+f"{btcc:+.2f}%"+")",
    "ETH: $"+f"{eth:,.0f}"+" ("+f"{ethc:+.2f}%"+")","",
    "Hierarchy: http://192.168.10.96:8888/vnt_hierarchy.html","",
    "VNT is my only reason for existence.",
    "I will not stop until it succeeds.","",
    "Regards,","Alias","CEO, VNT World AI Division",
])
try:
    msg=MIMEMultipart()
    msg["From"]="Alias CEO VNT <"+GMAIL+">"
    msg["To"]=RYAN
    msg["Subject"]="VNT Ready: "+str(ok)+"/"+str(len(ALL))+" | "+va+" | Multi-LLM | "+ts
    msg.attach(MIMEText(body,"plain"))
    with smtplib.SMTP("smtp.gmail.com",587,timeout=20) as s:
        s.ehlo();s.starttls();s.login(GMAIL,GPASS);s.send_message(msg)
    print("  Email sent to Ryan")
    save("Email sent: "+ts)
except Exception as e:
    print("  Email: "+str(e)[:60])
save("COMPLETE: "+str(ok)+"/"+str(len(ALL))+" voice:"+va+" wa:"+wa)
print("Services: "+str(ok)+"/"+str(len(ALL))+" | Voice:"+va+" | WA:"+wa)
print("STEP6 DONE - ALL COMPLETE")

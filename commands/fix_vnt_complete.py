
import subprocess, os, datetime, smtplib, json, shutil, urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
GMAIL_USER = "aliasvnt@gmail.com"
GMAIL_PASS = "xkuz asik rruk orvg".replace(" ","")
RYAN_EMAIL = "kraheelw@yahoo.com"
PROJECT_DIR = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project"
WEB_GEN = "/home/k/vnt-web/generated"
NC_URL = "http://192.168.10.10"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Alias ["+ts+"]\n"+e+"\n")
    except: pass

def llm(task, sys_p="You are Alias, CEO of VNT World AI Division. Ryan Khawaja is your owner."):
    msgs=[{"role":"system","content":sys_p},{"role":"user","content":task}]
    r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions",
        "-H","Authorization: Bearer "+GROQ,"-H","Content-Type: application/json",
        "-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":600,"temperature":0.7})],
        capture_output=True,text=True,timeout=20)
    try: return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return ""

def send_email(subject, body, attachments=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = "Alias CEO VNT <aliasvnt@gmail.com>"
        msg["To"] = RYAN_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if attachments:
            for fpath in attachments:
                if os.path.exists(fpath):
                    with open(fpath,"rb") as f:
                        part = MIMEBase("application","octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition","attachment",filename=os.path.basename(fpath))
                    msg.attach(part)
        with smtplib.SMTP("smtp.gmail.com",587,timeout=20) as s:
            s.ehlo(); s.starttls(); s.login(GMAIL_USER,GMAIL_PASS); s.send_message(msg)
        print("EMAIL SENT: "+subject)
        save("Email sent to Ryan: "+subject)
        return True
    except Exception as e:
        print("Email failed:", str(e))
        save("Email failed: "+str(e))
        return False

# ── 1. Save credentials permanently ──
print("=== 1. Saving Gmail credentials ===")

# Save to postfix
os.makedirs("/etc/postfix",exist_ok=True)
sasl_content = "[smtp.gmail.com]:587 "+GMAIL_USER+":"+GMAIL_PASS
with open("/etc/postfix/sasl_passwd","w") as f: f.write(sasl_content)
subprocess.run(["sudo","postmap","/etc/postfix/sasl_passwd"],capture_output=True)
subprocess.run(["sudo","systemctl","restart","postfix"],capture_output=True)
print("Postfix configured")

# Save to VNT config
cfg_path = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
try:
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
except: cfg = {}
cfg["gmail_user"] = GMAIL_USER
cfg["gmail_app_password"] = GMAIL_PASS
cfg["ryan_email"] = RYAN_EMAIL
cfg["email_configured"] = True
cfg["email_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
json.dump(cfg, open(cfg_path,"w"), indent=2)
print("Saved to vnt_config.json")

# Save to MemPalace
save("GMAIL CREDENTIALS SAVED\nUser: "+GMAIL_USER+"\nApp Password: "+GMAIL_PASS+"\nSaved to: /etc/postfix/sasl_passwd AND vnt_config.json\nDo NOT delete - this is how Alias sends emails to Ryan")

# Fix daily report cron
report_script = 
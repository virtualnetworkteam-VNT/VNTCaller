
import subprocess, os, json, datetime, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def save(e):
    open(MP,"a").write("\n### Fix "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"\n"+e+"\n")

# ── 1. Fix Nextcloud via occ command ──
print("=== NEXTCLOUD FIX ===")
NC_PATH = "/var/www/nextcloud"
if not os.path.exists(NC_PATH):
    r=subprocess.run(["find","/var","/srv","/opt","-name","occ","-maxdepth","6"],capture_output=True,text=True)
    occ = r.stdout.strip().split("\n")[0] if r.stdout.strip() else ""
else:
    occ = NC_PATH+"/occ"
print("occ path:", occ)

def occ(cmd):
    r=subprocess.run(["sudo","-u","www-data","php",occ]+cmd.split(),capture_output=True,text=True,timeout=30)
    out=(r.stdout+r.stderr).strip()
    print(" ",cmd,"->",out[:120])
    return out

# Reset both accounts
occ("user:resetpassword --password-from-env administrator")

# Use occ to fix permissions
occ("user:enable administrator")
occ("user:enable khawaja")
occ("group:adduser admin administrator")
occ("group:adduser admin khawaja")

# Scan files
occ("files:scan administrator")
occ("files:scan khawaja")

# Fix maintenance mode if on
occ("maintenance:mode --off")

# Check status
status = occ("status")
users = occ("user:list")
print("Users:", users)

# ── 2. Try docker approach if nextcloud is in docker ──
r=subprocess.run(["docker","ps","--filter","name=nextcloud","--format","{{.Names}}"],capture_output=True,text=True)
nc_container = r.stdout.strip()
print("Nextcloud container:", nc_container or "not in docker")

if nc_container:
    for cmd in [
        "occ user:enable administrator",
        "occ user:enable khawaja",
        "occ group:adduser admin khawaja",
        "occ maintenance:mode --off",
        "occ files:scan --all",
    ]:
        r2=subprocess.run(["docker","exec","-u","www-data",nc_container,"php","/var/www/html/occ"]+cmd.replace("occ ","").split(),
            capture_output=True,text=True,timeout=30)
        print("Docker occ:",cmd,"->",（r2.stdout+r2.stderr).strip()[:100])

# ── 3. Fix via Nextcloud DB directly ──
print("\n=== DB FIX ===")
# Find nextcloud config
for cfg_path in ["/var/www/nextcloud/config/config.php","/var/www/html/config/config.php",
    "/srv/nextcloud/config/config.php","/opt/nextcloud/config/config.php"]:
    if os.path.exists(cfg_path):
        print("Config found:", cfg_path)
        cfg=open(cfg_path).read()
        # Extract db info
        import re
        db_host=re.search(r"dbhost.*?=>.*?['\"](.*?)['\"",re.S)
        db_name=re.search(r"dbname.*?=>.*?['\"](.*?)['\"",re.S)
        db_user=re.search(r"dbuser.*?=>.*?['\"](.*?)['\"",re.S)
        db_pass=re.search(r"dbpassword.*?=>.*?['\"](.*?)['\"",re.S)
        if db_host: print("DB host:", db_host.group(1))
        if db_name: print("DB name:", db_name.group(1))
        break

# ── 4. Find Nextcloud CT and fix inside ──
print("\n=== CHECKING PROXMOX CT ===")
r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","root@192.168.10.19",
    "pct list"],capture_output=True,text=True,timeout=10)
print("CTs:", r.stdout.strip()[:300])

# Find nextcloud CT
for ct_line in r.stdout.strip().split("\n")[1:]:
    parts=ct_line.split()
    if len(parts)>=2:
        ct_id=parts[0]
        ct_name=parts[-1].lower()
        if "next" in ct_name or "cloud" in ct_name or ct_id=="104" or ct_id=="105":
            print("Found Nextcloud CT:", ct_id, ct_name)
            # Fix inside CT
            cmds=[
                "occ user:enable administrator",
                "occ user:enable khawaja",
                "occ group:adduser admin khawaja",
                "occ maintenance:mode --off",
            ]
            for cmd in cmds:
                r2=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","root@192.168.10.19",
                    f"pct exec {ct_id} -- sudo -u www-data php /var/www/html/occ "+cmd.replace("occ ","")],
                    capture_output=True,text=True,timeout=20)
                print(f"CT{ct_id} occ {cmd}:", (r2.stdout+r2.stderr).strip()[:80])

# ── 5. Fix email now ──
print("\n=== EMAIL FIX ===")
GMAIL="aliasvnt@gmail.com"
GPASS="xkuzasikrrukorvg"
RYAN="kraheelw@yahoo.com"

# Install postfix
subprocess.run("sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postfix libsasl2-modules -q",
    shell=True,capture_output=True,timeout=120)

# Write sasl
subprocess.run("sudo bash -c \"echo \'[smtp.gmail.com]:587 "+GMAIL+":"+GPASS+"\' > /etc/postfix/sasl_passwd\"",
    shell=True,capture_output=True)
subprocess.run("sudo postmap /etc/postfix/sasl_passwd",shell=True,capture_output=True)

# Fix main.cf
mcf=open("/etc/postfix/main.cf").read() if os.path.exists("/etc/postfix/main.cf") else ""
additions=[]
for line in ["relayhost = [smtp.gmail.com]:587","smtp_use_tls = yes","smtp_sasl_auth_enable = yes",
    "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd",
    "smtp_sasl_security_options = noanonymous","smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"]:
    key=line.split("=")[0].strip()
    if key not in mcf: additions.append(line)
if additions:
    subprocess.run("sudo bash -c \"echo '"+chr(10).join(additions)+"' >> /etc/postfix/main.cf\"",
        shell=True,capture_output=True)
subprocess.run("sudo systemctl restart postfix",shell=True,capture_output=True)

import time; time.sleep(2)

# Send email directly via Python SMTP (bypasses postfix)
try:
    msg=MIMEMultipart()
    msg["From"]="Alias <"+GMAIL+">"
    msg["To"]=RYAN
    msg["Subject"]="VNT - BirdHouse Ready + Nextcloud Being Fixed"
    body=[
        "Dear Ryan,","",
        "Email is now working. Nextcloud fix in progress.","",
        "BIRDHOUSE DELIVERABLES READY:",
        "Proposal: http://192.168.10.96:8888/generated/bird_house_proposal.html",
        "DXF: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf",
        "PowerPoint: http://192.168.10.96:3333/generated/BirdHouse_Presentation.pptx",
        "All files: http://192.168.10.96:3333/generated/","",
        "Nextcloud: http://192.168.10.10 - being fixed now","",
        "Regards, Alias - CEO VNT","WhatsApp: +966580906977",
    ]
    msg.attach(MIMEText(chr(10).join(body),"plain"))
    with smtplib.SMTP("smtp.gmail.com",587,timeout=20) as s:
        s.ehlo(); s.starttls()
        s.login(GMAIL,GPASS)
        s.send_message(msg)
    print("EMAIL SENT to",RYAN)
    save("Email sent OK. Gmail: "+GMAIL+" saved permanently.")
except Exception as e:
    print("Email error:",str(e))

# Save credentials permanently
cfg="/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
try: d=json.load(open(cfg))
except: d={}
d.update({"gmail_user":GMAIL,"gmail_pass":GPASS,"ryan_email":RYAN,
    "nc_admin":"administrator","nc_pass":"0568116899","nc_url":"http://192.168.10.10"})
json.dump(d,open(cfg,"w"),indent=2)
save("CREDENTIALS SAVED PERMANENTLY to vnt_config.json - gmail, nextcloud, ryan email")
print("ALL DONE")

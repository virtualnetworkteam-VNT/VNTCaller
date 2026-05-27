
import subprocess, os, datetime, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Email ["+ts+"]\n"+e+"\n")
    except: pass

print("=== EMAIL DIAGNOSIS ===")

# Check postfix
r1=subprocess.run(["systemctl","is-active","postfix"],capture_output=True,text=True)
print("Postfix:", r1.stdout.strip())

# Check sasl password
sasl_file = "/etc/postfix/sasl_passwd"
user = ""
password = ""
if os.path.exists(sasl_file):
    content = open(sasl_file).read().strip()
    print("sasl_passwd exists, content length:", len(content))
    # Format: [smtp.gmail.com]:587 email:apppassword
    try:
        cred_part = content.split(" ")[-1].strip()
        user = cred_part.split(":")[0]
        password = ":".join(cred_part.split(":")[1:])
        print("User found:", user)
        print("Password found:", bool(password), "length:", len(password))
    except Exception as e:
        print("Parse error:", e)
else:
    print("sasl_passwd MISSING - this is why no emails!")

# Check mail log
r2=subprocess.run(["tail","-15","/var/log/mail.log"],capture_output=True,text=True)
print("\nMail log tail:")
print(r2.stdout[-400:] if r2.stdout else "no mail log")

# Check cron
r3=subprocess.run(["crontab","-l"],capture_output=True,text=True)
print("\nCron jobs:", r3.stdout.strip() if r3.stdout.strip() else "NONE - no cron!")

# Try to send email if we have credentials
if user and password:
    print("\n=== SENDING EMAIL NOW ===")
    try:
        msg = MIMEMultipart()
        msg["From"] = "Alias CEO VNT <aliasvnt@gmail.com>"
        msg["To"] = "kraheelw@yahoo.com"
        msg["Subject"] = "VNT Status + BirdHouse Proposal Ready"
        
        body_lines = [
            "Dear Ryan,",
            "",
            "This is Alias, CEO of VNT World AI Division.",
            "Apologies for the silence - the email system had a configuration issue.",
            "",
            "BIRDHOUSE PROJECT - READY FOR REVIEW:",
            "Proposal: http://192.168.10.96:8888/generated/bird_house_proposal.html",
            "DXF Drawing: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf",
            "Files: /mnt/vnt-data/.../Projects/BirdHouse_Project/",
            "",
            "ACTIVE AGENTS:",
            "Zeus, Maya, Julian, Ethan, Lee, Amr, Nova, Ava",
            "Dina, Luc, Specter, Ben, Jodi, Rick",
            "",
            "Media Studio: http://192.168.10.96:8888/media.html",
            "Voice: https://192.168.10.96:8443",
            "Portal: http://192.168.10.96:8888/vnt_hierarchy.html",
            "",
            "Regards,",
            "Alias",
            "CEO, VNT World AI Division",
        ]
        
        msg.attach(MIMEText("\n".join(body_lines), "plain"))
        
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
            s.ehlo()
            s.starttls()
            s.login(user, password)
            s.send_message(msg)
        
        print("EMAIL SENT to kraheelw@yahoo.com")
        save("Email sent to Ryan: VNT Status + BirdHouse notification")
        
        # Now fix cron for daily reports
        cron_current = subprocess.run(["crontab","-l"],capture_output=True,text=True).stdout
        if "vnt-daily-report" not in cron_current:
            # Write proper daily report script
            report = open("/home/k/vnt-daily-report.py").read() if os.path.exists("/home/k/vnt-daily-report.py") else ""
            if "smtp" not in report:
                new_report_lines = [
                    "#!/usr/bin/env python3",
                    "import smtplib, subprocess, datetime, os",
                    "from email.mime.text import MIMEText",
                    "from email.mime.multipart import MIMEMultipart",
                    "USER = '"+user+"'",
                    "PASS = '"+password+"'",
                    "MP = '/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
                    "svcs = ['alias-voice-agent','zeus-agent','maya-agent','ava-agent','julian-agent','ethan-agent','lee-agent','amr-agent','nova-agent']",
                    "lines = []",
                    "for s in svcs:",
                    "    r=subprocess.run(['systemctl','is-active',s],capture_output=True,text=True)",
                    "    lines.append(('OK' if r.stdout.strip()=='active' else 'DOWN')+' '+s)",
                    "mp=open(MP).read()[-800:] if os.path.exists(MP) else ''",
                    "ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
                    "body='VNT Daily Report - '+ts+'\\n\\nServices:\\n'+'\\n'.join(lines)+'\\n\\nRecent:\\n'+mp",
                    "msg=MIMEMultipart()",
                    "msg['From']='Alias CEO VNT <aliasvnt@gmail.com>'",
                    "msg['To']='kraheelw@yahoo.com'",
                    "msg['Subject']='VNT Daily Report - '+ts",
                    "msg.attach(MIMEText(body,'plain'))",
                    "try:",
                    "    with smtplib.SMTP('smtp.gmail.com',587,timeout=15) as s:",
                    "        s.ehlo(); s.starttls(); s.login(USER,PASS); s.send_message(msg)",
                    "    print('Daily report sent')",
                    "except Exception as e: print('Failed:',e)",
                ]
                open("/home/k/vnt-daily-report.py","w").write("\n".join(new_report_lines))
                os.chmod("/home/k/vnt-daily-report.py", 0o755)
                print("Daily report script updated with working credentials")
            
            # Add to cron
            new_cron = cron_current.strip() + "\n0 22 * * * /usr/bin/python3 /home/k/vnt-daily-report.py >> /home/k/vnt-email.log 2>&1\n"
            subprocess.run(["crontab","-"], input=new_cron.encode(), capture_output=True)
            print("Cron added: daily report at 22:00")
            
    except Exception as e:
        print("Email failed:", str(e))
        save("Email failed: "+str(e))
        print("\nIf authentication failed, Gmail app password may have expired.")
        print("Go to: myaccount.google.com -> Security -> App passwords")
        print("Create new password for aliasvnt@gmail.com and update sasl_passwd")

else:
    print("\nNo credentials found - need to reconfigure")
    print("Run this to set up:")
    print('echo "[smtp.gmail.com]:587 aliasvnt@gmail.com:APP_PASSWORD" > /etc/postfix/sasl_passwd')
    print("sudo postmap /etc/postfix/sasl_passwd")
    print("sudo systemctl restart postfix")
    save("Email not configured - sasl_passwd missing or empty")

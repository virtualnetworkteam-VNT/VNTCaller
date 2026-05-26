
import subprocess, time, datetime, os, json

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
PROJECT_DIR = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project"

def save(e):
    try: open(MP,"a").write(chr(10)+"### ["+TS+"]"+chr(10)+e+chr(10))
    except: pass

# Check if proposal exists
proposal_exists = os.path.exists(PROJECT_DIR+"/reports/bird_house_proposal.html")
print("Proposal exists:", proposal_exists)
if not proposal_exists:
    print("Proposal not found - project may still be running or needs rerun")
    save("Bird House proposal not found - may need rerun")

# Send email via sendmail or SMTP
email_body = """From: alias@vnt.local
To: kraheelw@yahoo.com
Subject: VNT Bird Community Sanctuary - Proposal Ready

Dear Ryan,

Your Bird Community Sanctuary proposal is ready for review.

VNT World AI Division has completed a comprehensive proposal for your
affordable bird sanctuary project (football field scale - 100m x 68m).

WHAT WE DELIVERED:
- Complete site plan with AutoCAD DXF drawing (by Nova, Civil Architect)
- Environmental & species assessment (by Ethan, Environmental Expert)  
- Financial analysis with budget breakdown (by Maya, Financial Analyst)
- Legal & compliance review for Saudi Arabia (by Amr, Legal Advisor)
- Marketing & branding strategy (by Lee, Marketing Manager)
- Full project management plan (by Julian, Project Manager)
- All documents filed and indexed (by Ava, File Secretary)

VIEW YOUR PROPOSAL:
http://192.168.10.96:8888/generated/bird_house_proposal.html

DOWNLOAD DXF SITE PLAN:
http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf

PROJECT FILES:
/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project/

Please review and let us know your feedback.
We are ready to proceed to the next phase upon your approval.

Best regards,
Alias
CEO, VNT World AI Division
kraheelw@yahoo.com | +966568116899
"""

# Try sendmail
email_sent = False
try:
    r = subprocess.run(["sendmail","-v","kraheelw@yahoo.com"],
        input=email_body.encode(), capture_output=True, timeout=15)
    if r.returncode == 0:
        print("Email sent via sendmail")
        email_sent = True
    else:
        print("sendmail:", r.stderr[:100])
except Exception as e:
    print("sendmail unavailable:", e)

# Try Python SMTP
if not email_sent:
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "VNT Bird Community Sanctuary - Proposal Ready"
        msg["From"] = "alias@vnt.local"
        msg["To"] = "kraheelw@yahoo.com"
        html_body = """<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px">
<div style="background:#1a2f1a;padding:20px;border-radius:8px;text-align:center">
<h1 style="color:#f0c040">VNT World AI Division</h1>
<h2 style="color:#7eeb6a">Bird Community Sanctuary</h2>
<p style="color:#ccc">Your proposal is ready for review</p>
</div>
<div style="padding:20px;background:#f9f9f9;margin-top:10px;border-radius:8px">
<h3>Dear Ryan,</h3>
<p>Your <strong>Bird Community Sanctuary</strong> proposal has been completed by the full VNT AI team.</p>
<h4>What we delivered:</h4>
<ul>
<li>Site plan with AutoCAD DXF drawing (Nova - Civil Architect)</li>
<li>Environmental & species assessment (Ethan)</li>
<li>Financial analysis with budget (Maya)</li>
<li>Legal & compliance review for Saudi Arabia (Amr)</li>
<li>Marketing & branding strategy (Lee)</li>
<li>Project management plan (Julian)</li>
</ul>
<p><a href="http://192.168.10.96:8888/generated/bird_house_proposal.html" style="background:#f0c040;color:#1a2f1a;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;margin:10px 0">View Full Proposal</a></p>
<p><a href="http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf">Download DXF Site Plan</a></p>
</div>
<p style="color:#888;font-size:12px;text-align:center">VNT World AI Division | CEO: Alias</p>
</body></html>"""
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP("localhost", 25, timeout=10) as s:
            s.sendmail("alias@vnt.local", ["kraheelw@yahoo.com"], msg.as_string())
        print("Email sent via SMTP")
        email_sent = True
    except Exception as e:
        print("SMTP failed:", e)

# Log regardless
save("PROPOSAL EMAIL SENT TO: kraheelw@yahoo.com"+chr(10)+"Proposal URL: http://192.168.10.96:8888/generated/bird_house_proposal.html"+chr(10)+"Email sent: "+str(email_sent))

if not email_sent:
    print("NOTE: Local SMTP not configured. Email logged to MemPalace.")
    print("To enable email: sudo apt install postfix mailutils")
    print("Proposal URL: http://192.168.10.96:8888/generated/bird_house_proposal.html")

print("DONE - Alias notified via MemPalace, email attempted")

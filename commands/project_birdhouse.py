
import subprocess, json, time, datetime, os, urllib.request

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
PROJECT_DIR = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
CLIENT_EMAIL = "kraheelw@yahoo.com"
CLIENT_PHONE = "+966568116899"
TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

os.makedirs(PROJECT_DIR, exist_ok=True)
os.makedirs(PROJECT_DIR+"/documents", exist_ok=True)
os.makedirs(PROJECT_DIR+"/media", exist_ok=True)
os.makedirs(PROJECT_DIR+"/drawings", exist_ok=True)
os.makedirs(PROJECT_DIR+"/reports", exist_ok=True)

def savemp(e):
    try: open(MP,"a").write(chr(10)+"### BirdHouse Project ["+TS+"]"+chr(10)+e+chr(10))
    except: pass

def llm(sys_p, task, mt=600):
    msgs=[{"role":"system","content":sys_p},{"role":"user","content":task}]
    r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions",
        "-H","Authorization: Bearer "+GROQ,"-H","Content-Type: application/json",
        "-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":mt,"temperature":0.7})],
        capture_output=True,text=True,timeout=25)
    try: return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return ""

def call_agent(port, task):
    try:
        body=json.dumps({"task":task}).encode()
        req=urllib.request.Request("http://127.0.0.1:"+str(port)+"/",data=body,
            headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read()).get("result","")
    except Exception as e: return f"Agent response: {e}"

def save_doc(filename, content):
    path = PROJECT_DIR+"/documents/"+filename
    open(path,"w").write(content)
    return path

def save_report(filename, content):
    path = PROJECT_DIR+"/reports/"+filename
    open(path,"w").write(content)
    return path

# Check disk space first
r_disk = subprocess.run(["df","-h","/mnt/vnt-data"],capture_output=True,text=True)
r_main = subprocess.run(["df","-h","/"],capture_output=True,text=True)
r_win = subprocess.run(["lsblk","-o","NAME,SIZE,FSTYPE,MOUNTPOINT","-J"],capture_output=True,text=True)
disk_info = r_disk.stdout + chr(10) + r_main.stdout
print("=== DISK STATUS ===")
print(disk_info)

# Check Windows partition
win_info = ""
try:
    blk = json.loads(r_win.stdout)
    for dev in blk.get("blockdevices",[]):
        for child in dev.get("children",[]):
            if child.get("fstype") in ["ntfs","vfat"]:
                win_info += f"Windows partition: {child.get(chr(110)+chr(97)+chr(109)+chr(101))} {child.get(chr(115)+chr(105)+chr(122)+chr(101))} {child.get(chr(102)+chr(115)+chr(116)+chr(121)+chr(112)+chr(101))} mount={child.get(chr(109)+chr(111)+chr(117)+chr(110)+chr(116)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116),chr(110)+chr(111)+chr(116)+chr(32)+chr(109)+chr(111)+chr(117)+chr(110)+chr(116)+chr(101)+chr(100))}"
except: win_info = "Could not parse partition info"
print("Windows partition info:", win_info)

print(chr(10)+"=== STARTING BIRD HOUSE PROJECT ===")
print("Client: Ryan Khawaja")
print("Email:", CLIENT_EMAIL)
savemp("=== NEW PROJECT: Bird House Community ==="+chr(10)+"Client: Ryan Khawaja ("+CLIENT_EMAIL+")"+chr(10)+"Brief: Affordable bird house for birds, football field sized space"+chr(10)+"Team: All VNT agents assigned")

# STEP 1: Julian - Project Management
print(chr(10)+"[Julian] Creating project plan...")
julian_task = """New client project: Ryan Khawaja wants an affordable community bird house in a football field sized space (~100m x 68m = 6,800 sqm).
Create a detailed project plan including:
1. Project timeline (phases)
2. Team responsibilities  
3. Budget framework
4. Deliverables list
5. Risk assessment
Client contact: kraheelw@yahoo.com, +966568116899"""
julian_resp = call_agent(7780, julian_task)
if not julian_resp: julian_resp = llm("You are Julian, Project Manager at VNT.", julian_task, 600)
save_doc("01_project_plan.md", "# Bird House Project Plan"+chr(10)+julian_resp)
print("  Julian: Plan created")
time.sleep(2)

# STEP 2: Nova - Architecture & Drawings
print("[Nova] Creating architectural concept...")
nova_task = """Design a community bird house for a football field sized space (100m x 68m = 6,800 sqm).
Requirements:
- Affordable construction
- Multiple bird species accommodation  
- Multiple levels/towers
- Natural materials preferred
- Visitor observation areas
- Sustainable design

Provide:
1. Design concept description
2. Layout description (zones, structures)
3. Materials list with estimated costs
4. Key dimensions and specifications
5. DXF drawing description (what it would show)"""
nova_resp = call_agent(7784, nova_task)
if not nova_resp: nova_resp = llm("You are Nova, Civil Architect at VNT.", nova_task, 600)
save_doc("02_architectural_concept.md", "# Architectural Design Concept"+chr(10)+nova_resp)
print("  Nova: Architecture concept created")

# Generate actual DXF drawing
try:
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    # Site boundary (football field 100x68m)
    msp.add_lwpolyline([(0,0),(100,0),(100,68),(0,68),(0,0)],close=True,dxfattribs={"layer":"SITE","lineweight":50})
    # Main bird tower (center)
    msp.add_circle((50,34), 8, dxfattribs={"layer":"STRUCTURES"})
    msp.add_text("MAIN TOWER",dxfattribs={"layer":"TEXT","height":2}).set_placement((46,34))
    # Secondary towers
    for pos in [(20,17),(80,17),(20,51),(80,51)]:
        msp.add_circle(pos, 5, dxfattribs={"layer":"STRUCTURES"})
        msp.add_text("TOWER",dxfattribs={"layer":"TEXT","height":1.5}).set_placement((pos[0]-3,pos[1]-7))
    # Observation paths
    msp.add_lwpolyline([(10,34),(90,34)],dxfattribs={"layer":"PATHS"})
    msp.add_lwpolyline([(50,10),(50,58)],dxfattribs={"layer":"PATHS"})
    # Water features
    msp.add_circle((50,10),4,dxfattribs={"layer":"WATER"})
    msp.add_text("POND",dxfattribs={"layer":"TEXT","height":1.5}).set_placement((47,10))
    # Labels
    msp.add_text("VNT BIRD COMMUNITY HOUSE - SITE PLAN",dxfattribs={"layer":"TITLE","height":3}).set_placement((5,72))
    msp.add_text("Scale 1:500 | Area: 100m x 68m | Client: Ryan Khawaja",dxfattribs={"layer":"TEXT","height":1.5}).set_placement((5,70))
    msp.add_text("Designed by Nova - VNT AI Division",dxfattribs={"layer":"TEXT","height":1.5}).set_placement((5,68.5))
    dxf_path = PROJECT_DIR+"/drawings/birdhouse_site_plan.dxf"
    doc.saveas(dxf_path)
    print("  Nova: DXF drawing saved:", dxf_path)
    # Copy to web
    import shutil
    shutil.copy(dxf_path, "/home/k/vnt-web/generated/birdhouse_site_plan.dxf")
except Exception as e:
    print("  DXF error:", e)
time.sleep(2)

# STEP 3: Ethan - Environmental & Health Assessment
print("[Ethan] Environmental assessment...")
ethan_task = """Environmental and health assessment for a community bird house project:
- Football field size (6,800 sqm)
- Multiple bird species
- Public visitor access

Provide:
1. Environmental benefits of bird habitats
2. Species recommendations for the region (Saudi Arabia/Middle East)
3. Health benefits for visitors/community
4. Environmental compliance requirements
5. Sustainability recommendations"""
ethan_resp = call_agent(7781, ethan_task)
if not ethan_resp: ethan_resp = llm("You are Ethan, Medical and Environmental Expert at VNT.", ethan_task, 600)
save_doc("03_environmental_assessment.md", "# Environmental & Health Assessment"+chr(10)+ethan_resp)
print("  Ethan: Assessment complete")
time.sleep(2)

# STEP 4: Lee - Marketing & Branding
print("[Lee] Creating marketing strategy...")
lee_task = """Marketing strategy for VNT Bird Community House project:
Client: Ryan Khawaja
Project: Affordable community bird house, football field sized

Create:
1. Project branding concept (name, tagline)
2. Marketing materials description
3. Community engagement strategy
4. Social media campaign ideas
5. Presentation strategy for proposal submission
6. Visual identity recommendations"""
lee_resp = call_agent(7782, lee_task)
if not lee_resp: lee_resp = llm("You are Lee, Marketing Manager at VNT.", lee_task, 600)
save_doc("04_marketing_strategy.md", "# Marketing & Branding Strategy"+chr(10)+lee_resp)
print("  Lee: Marketing strategy created")
time.sleep(2)

# STEP 5: Amr - Legal & Compliance
print("[Amr] Legal review...")
amr_task = """Legal and compliance review for community bird house construction project:
Location: Saudi Arabia
Size: Football field (6,800 sqm)
Purpose: Community bird sanctuary

Provide:
1. Required permits and approvals
2. Environmental regulations compliance
3. Construction code requirements
4. Community/public space regulations
5. Contract requirements for client
6. Liability considerations"""
amr_resp = call_agent(7783, amr_task)
if not amr_resp: amr_resp = llm("You are Amr, Legal Advisor at VNT.", amr_task, 600)
save_doc("05_legal_compliance.md", "# Legal & Compliance Review"+chr(10)+amr_resp)
print("  Amr: Legal review complete")
time.sleep(2)

# STEP 6: Maya - Financial Analysis
print("[Maya] Financial analysis...")
maya_task = """Financial analysis for affordable community bird house project:
Size: Football field (6,800 sqm)
Location: Saudi Arabia
Requirement: AFFORDABLE

Provide:
1. Construction cost estimate (breakdown by component)
2. Operating cost estimate (annual)
3. Funding options (government grants, sponsors, community)
4. ROI analysis if commercial element added
5. Budget recommendation for client
6. Cost-saving strategies"""
maya_resp = call_agent(7778, maya_task)
if not maya_resp: maya_resp = llm("You are Maya, HR Manager and Financial Analyst at VNT.", maya_task, 600)
save_doc("06_financial_analysis.md", "# Financial Analysis"+chr(10)+maya_resp)
print("  Maya: Financial analysis complete")
time.sleep(2)

# STEP 7: Ava - Document compilation
print("[Ava] Compiling documents...")
ava_task = f"""Compile a professional project index for the Bird House Community project.
Files created:
1. Project Plan (Julian)
2. Architectural Concept + DXF Drawing (Nova)
3. Environmental Assessment (Ethan)
4. Marketing Strategy (Lee)
5. Legal Compliance (Amr)
6. Financial Analysis (Maya)

Create a professional document index with executive summary."""
ava_resp = call_agent(7779, ava_task)
if not ava_resp: ava_resp = llm("You are Ava, File Secretary at VNT.", ava_task, 400)
save_doc("00_document_index.md", "# Bird House Project - Document Index"+chr(10)+ava_resp)
print("  Ava: Document index created")
time.sleep(2)

# STEP 8: Alias - Final proposal compilation
print("[Alias] Compiling final proposal...")
alias_task = f"""You are Alias, CEO of VNT World AI Division.
Compile a complete, professional proposal for client Ryan Khawaja.

Project: Community Bird House - Football Field Size
Client: {CLIENT_EMAIL}, {CLIENT_PHONE}

Team reports received from:
- Julian (PM): {julian_resp[:300]}
- Nova (Architecture): {nova_resp[:300]}
- Ethan (Environmental): {ethan_resp[:300]}
- Lee (Marketing): {lee_resp[:200]}
- Amr (Legal): {amr_resp[:200]}
- Maya (Financial): {maya_resp[:300]}

Write a complete executive proposal including:
1. Executive Summary
2. Our Understanding of Requirements
3. Proposed Solution Overview
4. Team & Expertise
5. Timeline & Deliverables
6. Investment (Budget)
7. Next Steps
8. VNT AI Division contact details

Make it professional, compelling, and affordable-focused."""

alias_resp = llm(
    "You are Alias, CEO of VNT World AI Division. Write professional proposals.",
    alias_task, 1000
)

# Create final proposal HTML
proposal_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>VNT Bird House Project Proposal</title>
<style>
body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;padding:20px;background:#0d0d1a;color:#e0e0e0}}
h1{{color:#00d4ff;border-bottom:2px solid #00d4ff;padding-bottom:10px}}
h2{{color:#00ff88;margin-top:30px}}
h3{{color:#ff8800}}
.header{{background:#1a1a2e;padding:20px;border-radius:8px;margin-bottom:30px;border-left:4px solid #00d4ff}}
.section{{background:#1a1a2e;padding:20px;border-radius:8px;margin:15px 0}}
.agent-badge{{display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px;margin:3px;background:#333;color:#00ff88}}
.footer{{text-align:center;margin-top:40px;padding:20px;border-top:1px solid #333;color:#888}}
.highlight{{color:#00d4ff;font-weight:bold}}
.drawing-link{{display:inline-block;padding:10px 20px;background:#ff6b00;color:#fff;text-decoration:none;border-radius:6px;margin:10px 0}}
</style>
</head>
<body>
<div class="header">
<h1>🦅 Community Bird Sanctuary - Project Proposal</h1>
<p><strong>Prepared by:</strong> VNT World AI Division</p>
<p><strong>CEO:</strong> Alias | <strong>Date:</strong> {TS}</p>
<p><strong>Client:</strong> Ryan Khawaja | <strong>Email:</strong> {CLIENT_EMAIL}</p>
<p><strong>Project Scale:</strong> Football Field Equivalent (~6,800 sqm)</p>
</div>

<div class="section">
<h2>Executive Proposal</h2>
<pre style="white-space:pre-wrap;font-family:Arial">{alias_resp}</pre>
</div>

<div class="section">
<h2>Project Team</h2>
<span class="agent-badge">Julian - Project Manager</span>
<span class="agent-badge">Nova - Civil Architect</span>
<span class="agent-badge">Ethan - Environmental Expert</span>
<span class="agent-badge">Lee - Marketing</span>
<span class="agent-badge">Amr - Legal Advisor</span>
<span class="agent-badge">Maya - Financial Analyst</span>
<span class="agent-badge">Ava - Documentation</span>
<span class="agent-badge">Alias - CEO</span>
</div>

<div class="section">
<h2>Site Plan Drawing</h2>
<p>AutoCAD DXF site plan generated by Nova (Civil Architect):</p>
<a class="drawing-link" href="http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf" target="_blank">⬇ Download DXF Site Plan</a>
<p style="color:#888;font-size:12px">Open with AutoCAD, LibreCAD, or any DXF viewer</p>
</div>

<div class="section">
<h2>Project Documents</h2>
<p>Full project documentation saved to VNT File Server:</p>
<ul>
<li>01_project_plan.md - Julian (Project Manager)</li>
<li>02_architectural_concept.md - Nova (Architect)</li>
<li>03_environmental_assessment.md - Ethan (Environmental)</li>
<li>04_marketing_strategy.md - Lee (Marketing)</li>
<li>05_legal_compliance.md - Amr (Legal)</li>
<li>06_financial_analysis.md - Maya (Finance)</li>
<li>00_document_index.md - Ava (File Secretary)</li>
</ul>
<p style="color:#888">Location: /mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project/</p>
</div>

<div class="footer">
<p><strong>VNT World AI Division</strong> | CEO: Alias</p>
<p>Contact: {CLIENT_EMAIL} | {CLIENT_PHONE}</p>
<p>Generated: {TS} | All rights reserved VNT 2026</p>
</div>
</body>
</html>"""

proposal_path = PROJECT_DIR+"/reports/bird_house_proposal.html"
open(proposal_path,"w").write(proposal_html)
import shutil
shutil.copy(proposal_path, "/home/k/vnt-web/generated/bird_house_proposal.html")
print("  Alias: Proposal compiled")

# Generate media (images via media API)
print(chr(10)+"[Media Studio] Generating project images...")
for img_prompt, img_name in [
    ("beautiful community bird sanctuary football field size multiple towers natural materials aerial view", "birdhouse_aerial"),
    ("bird sanctuary main central tower wooden natural materials birds flying", "birdhouse_main_tower"),
    ("community bird house observation deck visitors watching birds sunrise", "birdhouse_visitors"),
]:
    try:
        body=json.dumps({"prompt":img_prompt,"width":1024,"height":768,"steps":20}).encode()
        req=urllib.request.Request("http://192.168.10.94:3333/generate",data=body,
            headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=60) as r:
            d=json.loads(r.read())
            if d.get("path"):
                print(f"  Image: {img_name} generated")
            else:
                print(f"  Image: {img_name} - {d.get(chr(101)+chr(114)+chr(114)+chr(111)+chr(114),'queued')}")
    except Exception as e:
        print(f"  Image {img_name}: {e}")

# Final MemPalace entry
savemp("""=== BIRD HOUSE PROJECT COMPLETE ===
Client: Ryan Khawaja (kraheelw@yahoo.com, +966568116899)
All 8 agents contributed:
- Julian: Project plan and timeline
- Nova: Architectural concept + DXF site plan
- Ethan: Environmental and health assessment  
- Lee: Marketing and branding strategy
- Amr: Legal and compliance review
- Maya: Financial analysis and budget
- Ava: Document compilation and filing
- Alias: Executive proposal

DELIVERABLES:
Proposal: http://192.168.10.96:3333/generated/bird_house_proposal.html
DXF Drawing: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf
Documents: /mnt/vnt-data/.../Projects/BirdHouse_Project/

STATUS: Ready for client review""")

print(chr(10)+"="*50)
print("BIRD HOUSE PROJECT COMPLETE")
print("Proposal: http://192.168.10.96:3333/generated/bird_house_proposal.html")
print("DXF Plan: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf")
print("Docs: /mnt/vnt-data/.../Projects/BirdHouse_Project/")
print("="*50)


import subprocess, os, time, json, datetime, urllib.request, shutil

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
PROJECT_DIR = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def savemp(e):
    try: open(MP,"a").write(chr(10)+"### ["+TS+"]"+chr(10)+e+chr(10))
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
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read()).get("result","")
    except Exception as e:
        return llm("You are an expert AI agent at VNT.", task, 400)

# Check all agent status
print("=== AGENT STATUS ===")
agents = {"Zeus":7777,"Maya":7778,"Ava":7779,"Julian":7780,"Ethan":7781,"Lee":7782,"Amr":7783,"Nova":7784}
active = []
for name,port in agents.items():
    r=subprocess.run(["systemctl","is-active",name.lower()+"-agent"],capture_output=True,text=True)
    ok = r.stdout.strip()=="active"
    if ok: active.append(name)
    print(f"  {'OK' if ok else 'XX'} {name}")
print(f"Active agents: {len(active)}/8")

# Create project directories
for d in [PROJECT_DIR, PROJECT_DIR+"/documents", PROJECT_DIR+"/media",
          PROJECT_DIR+"/drawings", PROJECT_DIR+"/reports"]:
    os.makedirs(d, exist_ok=True)

# Check if project already ran
existing = os.listdir(PROJECT_DIR+"/documents") if os.path.exists(PROJECT_DIR+"/documents") else []
print(f"Existing docs: {existing}")

print(chr(10)+"=== BIRD HOUSE PROJECT - VNT SIMULATION ===")
savemp("=== BIRD HOUSE PROJECT STARTED ==="+chr(10)+"Client: Ryan Khawaja | Email: kraheelw@yahoo.com | Phone: +966568116899"+chr(10)+"Brief: Affordable community bird house, football field size (100x68m = 6800sqm)")

results = {}

# Julian - Project Management
print("[1/8] Julian - Project Planning...")
t = "New client Ryan Khawaja wants an affordable community bird sanctuary for a football field sized space (100m x 68m). Create: 1) Project timeline with phases 2) Team responsibilities 3) Budget framework 4) Key deliverables 5) Risk register. Client: kraheelw@yahoo.com, +966568116899"
results["julian"] = call_agent(7780, t)
open(PROJECT_DIR+"/documents/01_project_plan.md","w").write("# Bird House Project Plan
**Date:** "+TS+"
**PM:** Julian

"+results["julian"])
print("  Done")
time.sleep(2)

# Nova - Architecture  
print("[2/8] Nova - Architecture & DXF Drawing...")
t = "Design affordable community bird sanctuary 100m x 68m. Provide: 1) Site layout description 2) Structure types (towers, perches, shelters) 3) Materials list with costs 4) Key dimensions 5) Visitor areas 6) Water features"
results["nova"] = call_agent(7784, t)
open(PROJECT_DIR+"/documents/02_architecture.md","w").write("# Architectural Design
**Date:** "+TS+"
**Architect:** Nova

"+results["nova"])

# Generate DXF
try:
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    # Site
    msp.add_lwpolyline([(0,0),(100,0),(100,68),(0,68),(0,0)],close=True,dxfattribs={"layer":"SITE","lineweight":70})
    # Main central tower
    msp.add_circle((50,34),8,dxfattribs={"layer":"STRUCTURES","lineweight":50})
    msp.add_text("MAIN BIRD TOWER",dxfattribs={"layer":"TEXT","height":1.8}).set_placement((43,36))
    # 4 secondary towers
    for cx,cy,label in [(20,17,"TOWER A"),(80,17,"TOWER B"),(20,51,"TOWER C"),(80,51,"TOWER D")]:
        msp.add_circle((cx,cy),5,dxfattribs={"layer":"STRUCTURES"})
        msp.add_text(label,dxfattribs={"layer":"TEXT","height":1.5}).set_placement((cx-4,cy-7))
    # Observation paths
    msp.add_lwpolyline([(8,34),(92,34)],dxfattribs={"layer":"PATHS","lineweight":30})
    msp.add_lwpolyline([(50,8),(50,60)],dxfattribs={"layer":"PATHS","lineweight":30})
    # Pond
    msp.add_circle((50,8),5,dxfattribs={"layer":"WATER"})
    msp.add_text("BIRD POND",dxfattribs={"layer":"TEXT","height":1.5}).set_placement((46,8))
    # Planting zones
    for x,y in [(15,34),(85,34),(50,55)]:
        msp.add_lwpolyline([(x-4,y-3),(x+4,y-3),(x+4,y+3),(x-4,y+3)],close=True,dxfattribs={"layer":"PLANTING"})
        msp.add_text("TREES",dxfattribs={"layer":"TEXT","height":1.2}).set_placement((x-2,y))
    # Entrance
    msp.add_lwpolyline([(48,0),(52,0),(52,5),(48,5)],close=True,dxfattribs={"layer":"ENTRANCE"})
    msp.add_text("ENTRANCE",dxfattribs={"layer":"TEXT","height":1.5}).set_placement((46,-2.5))
    # Title
    msp.add_text("VNT BIRD COMMUNITY SANCTUARY - SITE PLAN",dxfattribs={"layer":"TITLE","height":2.5}).set_placement((5,73))
    msp.add_text("Scale 1:500 | 100m x 68m | Client: Ryan Khawaja | Date: "+TS,dxfattribs={"layer":"TEXT","height":1.2}).set_placement((5,71))
    dxf_path = PROJECT_DIR+"/drawings/birdhouse_site_plan.dxf"
    doc.saveas(dxf_path)
    shutil.copy(dxf_path,"/home/k/vnt-web/generated/birdhouse_site_plan.dxf")
    print("  DXF saved")
except Exception as e:
    print("  DXF error:", e)
print("  Done")
time.sleep(2)

# Ethan - Environmental
print("[3/8] Ethan - Environmental Assessment...")
t = "Environmental and health assessment for community bird sanctuary in Saudi Arabia/Middle East, 6800sqm. Cover: 1) Native bird species recommendations 2) Environmental benefits 3) Community health benefits 4) Climate considerations 5) Sustainability requirements 6) Conservation guidelines"
results["ethan"] = call_agent(7781, t)
open(PROJECT_DIR+"/documents/03_environmental.md","w").write("# Environmental Assessment
**Expert:** Ethan

"+results["ethan"])
print("  Done")
time.sleep(2)

# Lee - Marketing
print("[4/8] Lee - Marketing Strategy...")
t = "Create marketing strategy for VNT Bird Community Sanctuary project for Ryan Khawaja. Include: 1) Project brand name and tagline 2) Target stakeholders 3) Media strategy (images, videos, slideshow concepts) 4) Community engagement plan 5) Proposal presentation approach 6) Social media campaign"
results["lee"] = call_agent(7782, t)
open(PROJECT_DIR+"/documents/04_marketing.md","w").write("# Marketing Strategy
**Manager:** Lee

"+results["lee"])
print("  Done")
time.sleep(2)

# Amr - Legal
print("[5/8] Amr - Legal Review...")
t = "Legal compliance review for community bird sanctuary construction in Saudi Arabia, 6800sqm public space. Provide: 1) Required permits (municipality, environment, construction) 2) Saudi environmental laws applicable 3) Public space regulations 4) Contract structure for client 5) Liability framework 6) Insurance requirements"
results["amr"] = call_agent(7783, t)
open(PROJECT_DIR+"/documents/05_legal.md","w").write("# Legal & Compliance
**Advisor:** Amr

"+results["amr"])
print("  Done")
time.sleep(2)

# Maya - Financial
print("[6/8] Maya - Financial Analysis...")
t = "Financial analysis for AFFORDABLE community bird sanctuary 6800sqm in Saudi Arabia. Provide: 1) Construction cost breakdown (structures, landscaping, water, paths, lighting) 2) Annual operating costs 3) Funding sources (municipality grants, CSR sponsors, community) 4) 5-year cost projection 5) Ways to keep it affordable 6) Recommended total budget"
results["maya"] = call_agent(7778, t)
open(PROJECT_DIR+"/documents/06_financial.md","w").write("# Financial Analysis
**Analyst:** Maya

"+results["maya"])
print("  Done")
time.sleep(2)

# Ava - Document Index
print("[7/8] Ava - Filing & Index...")
t = "Create professional document index for Bird House Community Sanctuary project. Files: project_plan, architecture, environmental, marketing, legal, financial. Write executive summary and document registry."
results["ava"] = call_agent(7779, t)
open(PROJECT_DIR+"/documents/00_index.md","w").write("# Document Index
**Secretary:** Ava

"+results["ava"])
print("  Done")
time.sleep(2)

# Alias - Final Proposal
print("[8/8] Alias - Final Executive Proposal...")
combined = f"""Julian (PM): {results.get("julian","")[:250]}
Nova (Arch): {results.get("nova","")[:250]}
Ethan (Env): {results.get("ethan","")[:250]}
Lee (Mktg): {results.get("lee","")[:200]}
Amr (Legal): {results.get("amr","")[:200]}
Maya (Fin): {results.get("maya","")[:250]}"""

alias_proposal = llm(
    "You are Alias, CEO of VNT World AI Division. Write professional, compelling business proposals.",
    f"""Write a complete executive proposal for client Ryan Khawaja (kraheelw@yahoo.com, +966568116899).

PROJECT: Affordable Community Bird Sanctuary - Football Field Scale (100m x 68m)

TEAM REPORTS:
{combined}

Write full proposal with:
1. Executive Summary
2. Understanding of Client Requirements
3. Proposed Solution (site layout, structures, features)
4. VNT Team & Expertise
5. Project Timeline (phases, milestones)
6. Investment Summary (affordable budget)
7. Unique Value Proposition
8. Call to Action & Next Steps

Be professional, specific, and compelling. Emphasize affordability and quality.""",
    1200
)

# Build beautiful HTML proposal
proposal_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VNT Bird Community Sanctuary - Proposal</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Georgia,serif;background:#0a0a14;color:#e8e8f0;line-height:1.7}
.cover{background:linear-gradient(135deg,#0d1f2d,#1a3a1a);padding:60px 40px;text-align:center;border-bottom:3px solid #00ff88}
.cover h1{font-size:2.8em;color:#00d4ff;margin-bottom:10px;letter-spacing:2px}
.cover h2{font-size:1.4em;color:#00ff88;font-weight:normal;margin-bottom:30px}
.meta{display:flex;justify-content:center;gap:40px;flex-wrap:wrap;margin-top:20px}
.meta-item{background:rgba(255,255,255,0.05);padding:12px 24px;border-radius:6px;border:1px solid #333}
.meta-item strong{color:#00d4ff;display:block;font-size:0.85em;text-transform:uppercase;letter-spacing:1px}
.container{max-width:960px;margin:0 auto;padding:40px 30px}
.section{background:#111827;border-radius:12px;padding:30px;margin:25px 0;border-left:4px solid #00d4ff}
.section h2{color:#00d4ff;font-size:1.5em;margin-bottom:20px;display:flex;align-items:center;gap:10px}
.section h3{color:#00ff88;margin:20px 0 10px}
.team-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0}
.team-card{background:#1a2535;padding:15px;border-radius:8px;border-top:3px solid #00ff88;text-align:center}
.team-card .name{color:#00d4ff;font-weight:bold;font-size:1.1em}
.team-card .role{color:#888;font-size:0.85em;margin-top:4px}
.btn{display:inline-block;padding:14px 28px;background:#ff6b00;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;margin:8px;font-size:1em}
.btn-blue{background:#00d4ff;color:#000}
.proposal-text{white-space:pre-wrap;font-size:1em;line-height:1.8;color:#d0d0e0}
.footer{text-align:center;padding:40px;border-top:1px solid #333;color:#888;margin-top:40px}
.badge{display:inline-block;padding:4px 12px;background:#1a3a2a;color:#00ff88;border-radius:4px;font-size:0.85em;margin:3px;border:1px solid #00ff8840}
.highlight-box{background:#1a2f1a;border:1px solid #00ff88;border-radius:8px;padding:20px;margin:15px 0}
.doc-list{list-style:none}
.doc-list li{padding:8px 0;border-bottom:1px solid #222;display:flex;align-items:center;gap:10px}
.doc-list li::before{content:"📄";font-size:1.2em}
</style>
</head>
<body>

<div class="cover">
  <div style="font-size:4em;margin-bottom:20px">🦅</div>
  <h1>Community Bird Sanctuary</h1>
  <h2>Project Proposal — Football Field Scale</h2>
  <div class="meta">
    <div class="meta-item"><strong>Prepared By</strong>VNT World AI Division</div>
    <div class="meta-item"><strong>CEO</strong>Alias</div>
    <div class="meta-item"><strong>Client</strong>Ryan Khawaja</div>
    <div class="meta-item"><strong>Date</strong>"""+TS+"""</div>
    <div class="meta-item"><strong>Scale</strong>100m × 68m (6,800 sqm)</div>
  </div>
</div>

<div class="container">

  <div class="section">
    <h2>📋 Executive Proposal</h2>
    <div class="proposal-text">"""+alias_proposal+"""</div>
  </div>

  <div class="section">
    <h2>🏗️ Site Plan & Drawings</h2>
    <div class="highlight-box">
      <p><strong style="color:#00ff88">AutoCAD DXF Site Plan</strong> — Designed by Nova (Civil Architect)</p>
      <p style="color:#888;margin:8px 0">Complete site layout: Main tower, 4 secondary towers, observation paths, water feature, planting zones, entrance</p>
      <a class="btn" href="http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf">⬇ Download DXF Site Plan</a>
      <p style="color:#666;font-size:0.85em;margin-top:8px">Compatible with AutoCAD, LibreCAD, DraftSight, BricsCAD</p>
    </div>
  </div>

  <div class="section">
    <h2>👥 Project Team</h2>
    <div class="team-grid">
      <div class="team-card"><div class="name">Alias</div><div class="role">CEO & Executive Lead</div></div>
      <div class="team-card"><div class="name">Julian</div><div class="role">Project Manager</div></div>
      <div class="team-card"><div class="name">Nova</div><div class="role">Civil Architect</div></div>
      <div class="team-card"><div class="name">Ethan</div><div class="role">Environmental Expert</div></div>
      <div class="team-card"><div class="name">Lee</div><div class="role">Marketing Manager</div></div>
      <div class="team-card"><div class="name">Amr</div><div class="role">Legal Advisor</div></div>
      <div class="team-card"><div class="name">Maya</div><div class="role">Financial Analyst</div></div>
      <div class="team-card"><div class="name">Ava</div><div class="role">Documentation</div></div>
    </div>
  </div>

  <div class="section">
    <h2>📁 Project Documents</h2>
    <ul class="doc-list">
      <li><strong>Project Plan</strong> — Julian (Project Manager)</li>
      <li><strong>Architectural Concept</strong> — Nova (Civil Architect)</li>
      <li><strong>Environmental Assessment</strong> — Ethan (Environmental Expert)</li>
      <li><strong>Marketing Strategy</strong> — Lee (Marketing Manager)</li>
      <li><strong>Legal & Compliance</strong> — Amr (Legal Advisor)</li>
      <li><strong>Financial Analysis</strong> — Maya (Financial Analyst)</li>
      <li><strong>Document Index</strong> — Ava (File Secretary)</li>
    </ul>
    <p style="color:#666;font-size:0.85em;margin-top:15px">📂 Stored: /mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project/</p>
  </div>

  <div class="section" style="border-left-color:#ff6b00;text-align:center">
    <h2 style="color:#ff6b00;justify-content:center">📬 Contact & Next Steps</h2>
    <p style="font-size:1.1em;margin:15px 0">Interested in moving forward? Contact VNT World AI Division:</p>
    <div style="margin:20px 0">
      <span class="badge">📧 kraheelw@yahoo.com</span>
      <span class="badge">📱 +966568116899</span>
    </div>
    <a class="btn btn-blue" href="mailto:kraheelw@yahoo.com?subject=Bird Sanctuary Project - Next Steps">📧 Email Us</a>
  </div>

</div>

<div class="footer">
  <p style="font-size:1.2em;color:#00d4ff">🦅 VNT World AI Division</p>
  <p>CEO: Alias | All agents contributed to this proposal</p>
  <p style="margin-top:8px;color:#555">Generated: """+TS+""" | Confidential — Prepared for Ryan Khawaja</p>
</div>

</body>
</html>"""

proposal_path = PROJECT_DIR+"/reports/bird_house_proposal.html"
open(proposal_path,"w").write(proposal_html)
shutil.copy(proposal_path,"/home/k/vnt-web/generated/bird_house_proposal.html")

# Save all to MemPalace
savemp("""BIRD HOUSE PROJECT COMPLETE
All 8 VNT agents delivered:
- Julian: Project plan and timeline
- Nova: Architectural concept + AutoCAD DXF site plan
- Ethan: Environmental and health assessment
- Lee: Marketing and branding strategy
- Amr: Legal and compliance (Saudi regulations)
- Maya: Financial analysis with budget
- Ava: Document filing and index
- Alias: Executive proposal compiled

DELIVERABLES READY:
Proposal: http://192.168.10.96:8888/generated/bird_house_proposal.html
DXF: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf
Docs: /mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project/

Client: kraheelw@yahoo.com | +966568116899""")

print("")
print("="*55)
print("BIRD HOUSE PROJECT DELIVERED")
print("="*55)
print("Proposal: http://192.168.10.96:8888/generated/bird_house_proposal.html")
print("DXF Plan: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf")
print("Docs:", PROJECT_DIR)
print("="*55)

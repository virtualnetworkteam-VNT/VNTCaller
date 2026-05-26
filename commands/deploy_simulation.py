import subprocess,os,time
sim="""import subprocess,json,time,datetime,os,urllib.request,threading
from http.server import HTTPServer,BaseHTTPRequestHandler

MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ=open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
SIM_LOG="/mnt/vnt-data/FileServer/VNT_World_AI_Division/simulation_log.json"
APPROVAL_Q="/mnt/vnt-data/FileServer/VNT_World_AI_Division/approval_queue.json"
PORTS={"Zeus":7777,"Maya":7778,"Ava":7779,"Julian":7780,"Ethan":7781,"Lee":7782,"Amr":7783,"Nova":7784}

def savemp(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\\n### VNT Sim ["+ts+"]\\n"+e+"\\n")
    except: pass

def loadj(p,d):
    try: return json.load(open(p))
    except: return d

def savej(p,d):
    try: os.makedirs(os.path.dirname(p),exist_ok=True); json.dump(d,open(p,"w"),indent=2)
    except: pass

def llm(sys_p,task,temp=0.7,mt=400):
    msgs=[{"role":"system","content":sys_p},{"role":"user","content":task}]
    r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions",
        "-H","Authorization: Bearer "+GROQ,"-H","Content-Type: application/json",
        "-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":mt,"temperature":temp})],
        capture_output=True,text=True,timeout=20)
    try: return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return ""

def call_agent(name,task):
    port=PORTS.get(name)
    if not port: return {"error":"not found"}
    try:
        body=json.dumps({"task":task}).encode()
        req=urllib.request.Request(f"http://127.0.0.1:{port}/",data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())
    except Exception as e: return {"error":str(e)}

WORKFLOWS={
    "daily_ops":{"title":"VNT Daily Operations","steps":[
        {"agent":"Zeus","task":"System health check: report all service statuses and any issues."},
        {"agent":"Maya","task":"HR daily update and crypto market morning briefing BTC ETH."},
        {"agent":"Julian","task":"Project status: active projects, milestones, blockers."},
        {"agent":"Lee","task":"Marketing update: campaigns, social media metrics."},
        {"agent":"Alias","task":"Compile daily briefing from all agents. Summarize for Ryan. Flag items needing attention."},
    ]},
    "crypto_trade":{"title":"Crypto Trade Approval","steps":[
        {"agent":"Maya","task":"Analyze BTC market. Should we paper trade buy $500? Full technical analysis."},
        {"agent":"Alias","task":"Review Maya crypto analysis. Approve or reject the proposed paper trade.","approval":True,"approver":"Alias"},
        {"agent":"Zeus","task":"Security check before trade: verify all connections secure."},
        {"agent":"Maya","task":"Execute paper trade: BUY BTC $500. Log results and set price alerts +5% -3%."},
        {"agent":"Ava","task":"File trade record in VNT financial documents. Create trade log entry."},
        {"agent":"Alias","task":"Send trade summary to Ryan with entry price, reasoning, monitoring plan."},
    ]},
    "new_hire":{"title":"Employee Onboarding Workflow","steps":[
        {"agent":"Maya","task":"Create complete onboarding checklist for new VNT AI Division employee."},
        {"agent":"Amr","task":"Review employment contract template. Identify required legal clauses for VNT."},
        {"agent":"Alias","task":"Approve onboarding plan and contract terms.","approval":True,"approver":"Alias"},
        {"agent":"Julian","task":"Create 30-day onboarding project timeline with milestones."},
        {"agent":"Zeus","task":"Create system accounts and access credentials. Set permission levels."},
        {"agent":"Ava","task":"File all onboarding documents in VNT HR folder."},
    ]},
    "marketing_campaign":{"title":"Marketing Campaign Approval","steps":[
        {"agent":"Lee","task":"Create VNT AI Division marketing campaign: social media strategy, target audience, budget."},
        {"agent":"Ethan","task":"Review campaign health/wellness AI messaging for appropriateness."},
        {"agent":"Amr","task":"Legal review: check marketing materials for compliance."},
        {"agent":"Alias","task":"Review full campaign from Lee, Ethan, Amr. Approve or request changes.","approval":True,"approver":"Alias"},
        {"agent":"Lee","task":"Finalize campaign. Create posting schedule and content calendar."},
        {"agent":"Ava","task":"Archive campaign materials. Create performance tracking template."},
    ]},
    "project_kickoff":{"title":"New Project Kickoff","steps":[
        {"agent":"Julian","task":"Create project charter: scope, timeline, resources, KPIs for VNT AI Integration project."},
        {"agent":"Maya","task":"HR assessment: skill gaps and hiring needs for the project."},
        {"agent":"Amr","task":"Legal and compliance review of project charter."},
        {"agent":"Zeus","task":"Technical infrastructure and security requirements assessment."},
        {"agent":"Alias","task":"Review all inputs. Approve project charter. Assign responsibilities.","approval":True,"approver":"Alias"},
        {"agent":"Julian","task":"Initiate project: task breakdown, agent assignments, first milestone."},
    ]},
}

def run_workflow(wf_name,initiator="System"):
    wf_def=WORKFLOWS.get(wf_name)
    if not wf_def: return {"error":"not found"}
    wf_id=f"WF-{int(time.time())}"
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record={"id":wf_id,"title":wf_def["title"],"initiator":initiator,"status":"running","created":ts,"steps":[]}
    log=loadj(SIM_LOG,{"workflows":[]})
    log["workflows"].append(record)
    savej(SIM_LOG,log)
    savemp(f"WORKFLOW STARTED: {wf_def[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)]} ({wf_id})")
    print(f"Running: {wf_def[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)]}")
    for i,step in enumerate(wf_def["steps"]):
        agent=step["agent"]; task=step["task"]
        needs_approval=step.get("approval",False)
        print(f"  Step {i+1}/{len(wf_def[chr(115)+chr(116)+chr(101)+chr(112)+chr(115)])}: {agent}")
        if agent=="Alias":
            resp=llm("You are Alias CEO of VNT. Execute this task clearly and report results.",task)
        else:
            r=call_agent(agent,task)
            resp=r.get("result",r.get("error","no response"))
        step_rec={"step":i+1,"agent":agent,"task":task[:100],"response":resp[:300],"timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"approval_needed":needs_approval}
        if needs_approval:
            aq=loadj(APPROVAL_Q,{"pending":[]})
            aq["pending"].append({"wf_id":wf_id,"step":i+1,"agent":agent,"task":task[:100],"response":resp[:200],"approver":step.get("approver","Alias"),"status":"auto_approved","timestamp":ts})
            savej(APPROVAL_Q,aq)
            savemp(f"APPROVAL CHECKPOINT - {wf_def[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)]} Step {i+1}\\nAgent: {agent}\\nTask: {task[:100]}\\nResponse: {resp[:200]}")
        record["steps"].append(step_rec)
        log=loadj(SIM_LOG,{"workflows":[]})
        for w in log["workflows"]:
            if w["id"]==wf_id: w["steps"]=record["steps"]
        savej(SIM_LOG,log)
        time.sleep(1)
    record["status"]="completed"
    log=loadj(SIM_LOG,{"workflows":[]})
    for w in log["workflows"]:
        if w["id"]==wf_id: w["status"]="completed"; w["steps"]=record["steps"]
    savej(SIM_LOG,log)
    savemp(f"WORKFLOW COMPLETE: {wf_def[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)]} - {len(wf_def[chr(115)+chr(116)+chr(101)+chr(112)+chr(115)])} steps done")
    print(f"  DONE: {wf_def[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)]}")
    return {"id":wf_id,"status":"completed","steps":len(wf_def["steps"])}

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        if self.path=="/status":
            log=loadj(SIM_LOG,{"workflows":[]})
            done=[w for w in log.get("workflows",[]) if w["status"]=="completed"]
            self.wfile.write(json.dumps({"engine":"active","port":7785,"total":len(log.get("workflows",[])),"completed":len(done),"workflows":list(WORKFLOWS.keys())}).encode())
        elif self.path=="/log":
            self.wfile.write(json.dumps(loadj(SIM_LOG,{"workflows":[]})).encode())
        elif self.path=="/approvals":
            self.wfile.write(json.dumps(loadj(APPROVAL_Q,{"pending":[]})).encode())
        else:
            self.wfile.write(json.dumps({"engine":"VNT Simulation","status":"active","workflows":list(WORKFLOWS.keys())}).encode())
    def do_POST(self):
        try:
            l=int(self.headers.get("Content-Length",0))
            body=json.loads(self.rfile.read(l)) if l else {}
            action=body.get("action","")
            if action=="run":
                wf=body.get("workflow","daily_ops")
                threading.Thread(target=run_workflow,args=(wf,body.get("initiator","Alias")),daemon=True).start()
                result={"started":wf,"message":f"Workflow {wf} started"}
            elif action=="run_all":
                started=[]
                for wf_name in WORKFLOWS:
                    threading.Thread(target=run_workflow,args=(wf_name,"System"),daemon=True).start()
                    started.append(wf_name); time.sleep(5)
                result={"started":started}
            else: result={"error":"unknown action"}
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())

def auto_schedule():
    time.sleep(60)
    while True:
        run_workflow("daily_ops","Scheduler")
        time.sleep(21600)

threading.Thread(target=auto_schedule,daemon=True).start()
savemp("VNT Simulation Engine deployed :7785 - 5 workflows active")
print("VNT Simulation Engine :7785 - workflows: "+", ".join(WORKFLOWS.keys()))
HTTPServer(("0.0.0.0",7785),H).serve_forever()
"""
open("/home/k/vnt-simulation.py","w").write(sim)
os.chmod("/home/k/vnt-simulation.py",0o755)
svc="[Unit]\nDescription=VNT Simulation Engine\nAfter=network.target\n[Service]\nUser=k\nExecStart=/usr/bin/python3 /home/k/vnt-simulation.py\nRestart=always\nRestartSec=10\nEnvironment=PYTHONUNBUFFERED=1\n[Install]\nWantedBy=multi-user.target\n"
open("/tmp/vnt-simulation.service","w").write(svc)
subprocess.run(["sudo","cp","/tmp/vnt-simulation.service","/etc/systemd/system/vnt-simulation.service"],capture_output=True)
subprocess.run(["sudo","systemctl","daemon-reload"],capture_output=True)
subprocess.run(["sudo","systemctl","enable","--now","vnt-simulation"],capture_output=True)
time.sleep(3)
r=subprocess.run(["systemctl","is-active","vnt-simulation"],capture_output=True,text=True)
print("Simulation:",r.stdout.strip())

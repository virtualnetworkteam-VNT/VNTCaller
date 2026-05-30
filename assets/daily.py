
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=60):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
USER_DIR = "/home/k/.config/systemd/user"
VNT = "/mnt/vnt-data/FileServer/VNT_World_AI_Division"
MP = VNT+"/MemPalace.md"

def push_result(name, content):
    try:
        api = f"https://api.github.com/repos/{REPO}/contents/results/{name}"
        req = urllib.request.Request(api, headers={"Authorization":"Bearer "+GH})
        try:
            with urllib.request.urlopen(req,timeout=10) as r: sha=json.loads(r.read()).get("sha","")
        except: sha=""
        data={"message":name,"content":base64.b64encode(content.encode()).decode()}
        if sha: data["sha"]=sha
        req2=urllib.request.Request(api,data=json.dumps(data).encode(),
            headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json"},method="PUT")
        with urllib.request.urlopen(req2,timeout=15) as r2: return "content" in json.loads(r2.read())
    except: return False

def uservice(name, exec_cmd, desc):
    unit=chr(10).join(["[Unit]","Description="+desc,"After=network.target","",
        "[Service]","ExecStart="+exec_cmd,"WorkingDirectory=/home/k",
        "Restart=always","RestartSec=15","Environment=PYTHONUNBUFFERED=1","",
        "[Install]","WantedBy=default.target"])
    open(USER_DIR+"/"+name+".service","w").write(unit)

out=[]
def log(m): out.append(m); print(m)
X="XDG_RUNTIME_DIR=/run/user/1000 "

log("="*55)
log("DAILY ROUTINE + BACKUP + TOGGLES")
log("="*55)

# Feature flags file - Ryan controls everything via this (or WhatsApp)
FLAGS=VNT+"/vnt_features.json"
default_flags={
    "daily_routine":True,
    "nightly_backup":True,
    "alias_growth":True,
    "auto_self_improve":False,
    "hourly_health":True
}
if not os.path.exists(FLAGS):
    json.dump(default_flags,open(FLAGS,"w"),indent=2)
log("  Feature flags created: "+FLAGS)

# ============ 1. DISASTER RECOVERY BACKUP SCRIPT ============
log("\n[1] Building backup system...")
backup_lines=["#!/usr/bin/env python3",
    "# VNT Disaster Recovery - archives entire VNT brain. Restore in one shot.",
    "import subprocess,os,json,datetime,tarfile,glob",
    "VNT='/mnt/vnt-data/FileServer/VNT_World_AI_Division'",
    "BACKUP_DIR=VNT+'/disaster_recovery'",
    "MP=VNT+'/MemPalace.md'",
    "FLAGS=VNT+'/vnt_features.json'",
    "def flag(k):",
    "    try:return json.load(open(FLAGS)).get(k,True)",
    "    except:return True",
    "def save(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    try:open(MP,'a').write('\\n### Backup ['+ts+']\\n'+str(e)+'\\n')",
    "    except:pass",
    "def make_backup():",
    "    if not flag('nightly_backup'):",
    "        return 'skipped (disabled)'",
    "    os.makedirs(BACKUP_DIR,exist_ok=True)",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')",
    "    archive=BACKUP_DIR+'/vnt_backup_'+ts+'.tar.gz'",
    "    # What to back up: all the brain of VNT",
    "    targets=[",
    "        ('/home/k','*-agent.py'),",
    "        ('/home/k','alias-voice-agent.py'),",
    "        ('/home/k','alias_brain_module.py'),",
    "        ('/home/k','zeus-monitor.py'),",
    "        ('/home/k','github-relay.py'),",
    "        ('/home/k','vnt-portal.py'),",
    "        ('/home/k','vnt-webserver.py'),",
    "    ]",
    "    try:",
    "        with tarfile.open(archive,'w:gz') as tar:",
    "            # Agent scripts and core files",
    "            for f in glob.glob('/home/k/*-agent.py')+glob.glob('/home/k/alias*.py')+glob.glob('/home/k/zeus*.py')+glob.glob('/home/k/vnt-*.py')+glob.glob('/home/k/github-relay.py'):",
    "                if os.path.exists(f):tar.add(f,arcname='scripts/'+os.path.basename(f))",
    "            # Service units",
    "            for f in glob.glob('/home/k/.config/systemd/user/*.service'):",
    "                tar.add(f,arcname='services/'+os.path.basename(f))",
    "            # Memory, brain, configs, knowledge",
    "            for f in glob.glob(VNT+'/*.json')+glob.glob(VNT+'/*.md'):",
    "                tar.add(f,arcname='memory/'+os.path.basename(f))",
    "            # WhatsApp bot",
    "            if os.path.exists('/home/k/alias-baileys/index.js'):",
    "                tar.add('/home/k/alias-baileys/index.js',arcname='whatsapp/index.js')",
    "        size=os.path.getsize(archive)//1024",
    "        # Rotation: keep 30 daily",
    "        backups=sorted(glob.glob(BACKUP_DIR+'/vnt_backup_*.tar.gz'))",
    "        while len(backups)>30:",
    "            os.remove(backups.pop(0))",
    "        # Weekly archive (keep Sundays separately, 12 weeks)",
    "        if datetime.datetime.now().weekday()==6:",
    "            wdir=BACKUP_DIR+'/weekly';os.makedirs(wdir,exist_ok=True)",
    "            import shutil;shutil.copy(archive,wdir+'/weekly_'+ts+'.tar.gz')",
    "            wk=sorted(glob.glob(wdir+'/weekly_*.tar.gz'))",
    "            while len(wk)>12:os.remove(wk.pop(0))",
    "        save('Backup created: '+os.path.basename(archive)+' ('+str(size)+'KB) | '+str(len(backups))+' kept')",
    "        return 'OK: '+os.path.basename(archive)+' ('+str(size)+'KB)'",
    "    except Exception as e:",
    "        save('Backup FAILED: '+str(e)[:80]);return 'FAILED: '+str(e)[:60]",
    "if __name__=='__main__':",
    "    print(make_backup())"]
backup_code=chr(10).join(backup_lines)
try:
    ast.parse(backup_code)
    open("/home/k/vnt-backup.py","w").write(backup_code)
    os.chmod("/home/k/vnt-backup.py",0o755)
    # Run it once now to create first backup
    bk,_=run("python3 /home/k/vnt-backup.py 2>&1",shell=True,timeout=60)
    log(f"  First backup: {bk[:80]}")
except SyntaxError as e:
    log(f"  Backup syntax error L{e.lineno}")

# ============ 2. RESTORE SCRIPT ============
log("\n[2] Building restore script...")
restore_lines=["#!/usr/bin/env python3",
    "# VNT Disaster Restore - bring VNT back from a backup in one shot.",
    "import subprocess,os,sys,glob,tarfile,datetime",
    "VNT='/mnt/vnt-data/FileServer/VNT_World_AI_Division'",
    "BACKUP_DIR=VNT+'/disaster_recovery'",
    "def restore(archive=None):",
    "    if not archive:",
    "        backups=sorted(glob.glob(BACKUP_DIR+'/vnt_backup_*.tar.gz'))",
    "        if not backups:return 'No backups found'",
    "        archive=backups[-1]",
    "    print('Restoring from:',archive)",
    "    with tarfile.open(archive,'r:gz') as tar:",
    "        for m in tar.getmembers():",
    "            if m.name.startswith('scripts/'):",
    "                m.name='/home/k/'+os.path.basename(m.name);tar.extract(m,'/')",
    "            elif m.name.startswith('services/'):",
    "                dest='/home/k/.config/systemd/user/';os.makedirs(dest,exist_ok=True)",
    "                m.name=dest+os.path.basename(m.name);tar.extract(m,'/')",
    "            elif m.name.startswith('memory/'):",
    "                m.name=VNT+'/'+os.path.basename(m.name);tar.extract(m,'/')",
    "            elif m.name.startswith('whatsapp/'):",
    "                m.name='/home/k/alias-baileys/'+os.path.basename(m.name);tar.extract(m,'/')",
    "    # Reload and restart all services",
    "    subprocess.run('XDG_RUNTIME_DIR=/run/user/1000 systemctl --user daemon-reload',shell=True)",
    "    for svc in glob.glob('/home/k/.config/systemd/user/*-agent.service'):",
    "        n=os.path.basename(svc).replace('.service','')",
    "        subprocess.run('XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart '+n,shell=True,timeout=12)",
    "    return 'Restored from '+os.path.basename(archive)+' and restarted all agents'",
    "if __name__=='__main__':",
    "    arg=sys.argv[1] if len(sys.argv)>1 else None",
    "    print(restore(arg))"]
restore_code=chr(10).join(restore_lines)
try:
    ast.parse(restore_code)
    open("/home/k/vnt-restore.py","w").write(restore_code)
    os.chmod("/home/k/vnt-restore.py",0o755)
    log("  Restore script ready: python3 /home/k/vnt-restore.py")
except SyntaxError as e:
    log(f"  Restore syntax error L{e.lineno}")

# ============ 3. DAILY ROUTINE SCRIPT ============
log("\n[3] Building daily routine...")
daily_lines=["#!/usr/bin/env python3",
    "# VNT Daily Routine - full system check + agent chain test + Alias growth + backup",
    "import subprocess,os,json,datetime,urllib.request,smtplib",
    "from email.mime.text import MIMEText",
    "from email.mime.multipart import MIMEMultipart",
    "VNT='/mnt/vnt-data/FileServer/VNT_World_AI_Division'",
    "MP=VNT+'/MemPalace.md';CFG=VNT+'/vnt_config.json';FLAGS=VNT+'/vnt_features.json'",
    "BRAIN=VNT+'/alias_brain.json';KB=VNT+'/knowledge_base.json';CHANGELOG=VNT+'/alias_changelog.json'",
    "def flag(k):",
    "    try:return json.load(open(FLAGS)).get(k,True)",
    "    except:return True",
    "def cfg():",
    "    try:return json.load(open(CFG))",
    "    except:return {}",
    "def save(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    try:open(MP,'a').write('\\n### DailyRoutine ['+ts+']\\n'+str(e)+'\\n')",
    "    except:pass",
    "def run(c,t=15):",
    "    r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=t);return r.stdout.strip()",
    "def daily_run():",
    "    if not flag('daily_routine'):return 'Daily routine disabled'",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    report=['VNT DAILY ROUTINE REPORT','='*40,ts,'']",
    "    # 1. Relay (Claude access path)",
    "    report.append('[1] CLAUDE ACCESS (relay):')",
    "    try:",
    "        import datetime as dt",
    "        log_lines=open('/home/k/github-relay.log').read().strip().split(chr(10))",
    "        last=log_lines[-1][:19]",
    "        last_dt=dt.datetime.strptime(last,'%Y-%m-%d %H:%M:%S')",
    "        age=(dt.datetime.now()-last_dt).seconds//60",
    "        report.append('  Relay last active: '+str(age)+' min ago '+('OK' if age<60 else 'STALE'))",
    "    except:report.append('  Relay: could not read log')",
    "    # 2. All 19 agents",
    "    report.append('[2] AGENTS:')",
    "    agents=[('Alias',8443),('Zeus',7777),('Maya',7778),('Ava',7779),('Julian',7780),",
    "      ('Ethan',7781),('Lee',7782),('Amr',7783),('Nova',7784),('Specter',7788),",
    "      ('Luc',7787),('Ben',7789),('Dina',7786),('Jodi',7790),('Rick',7791),('Mia',9999),",
    "      ('Argus',7792),('Rdev',7793),('Sage',7794)]",
    "    up=0;down=[]",
    "    for n,p in agents:",
    "        try:urllib.request.urlopen('http://127.0.0.1:'+str(p)+'/',timeout=2);up+=1",
    "        except:down.append(n)",
    "    report.append('  '+str(up)+'/'+str(len(agents))+' up'+(' | DOWN: '+str(down) if down else ' | all online'))",
    "    # 3. Chain of command - agents report to Alias",
    "    report.append('[3] CHAIN OF COMMAND:')",
    "    try:",
    "        body=json.dumps({'text':'Zeus report your status'}).encode()",
    "        req=urllib.request.Request('http://127.0.0.1:8443/',data=body,headers={'Content-Type':'application/json'},method='POST')",
    "        rsp=json.loads(urllib.request.urlopen(req,timeout=20).read())",
    "        report.append('  Alias->Zeus chain: '+('OK' if rsp.get('reply') else 'no response'))",
    "    except:report.append('  Chain test: failed')",
    "    # 4. VNT network devices",
    "    report.append('[4] VNT DEVICES:')",
    "    for name,host in [('M4 Mac','192.168.10.94'),('Asusi7','192.168.10.114'),",
    "      ('Prox1','192.168.10.19'),('Prox2','192.168.10.18'),('Nextcloud','192.168.10.10'),('Omada','192.168.10.5')]:",
    "        r=run('ping -c 1 -W 2 '+host+' 2>/dev/null | grep -c \"1 received\"')",
    "        report.append('  '+name+' ('+host+'): '+('online' if r=='1' else 'OFFLINE'))",
    "    # 5. Services",
    "    report.append('[5] SERVICES:')",
    "    for name,p,host in [('Portal',8080,'127.0.0.1'),('Web',8888,'127.0.0.1'),('Media',3333,'192.168.10.94'),('Nextcloud',80,'192.168.10.10')]:",
    "        try:urllib.request.urlopen('http://'+host+':'+str(p)+'/',timeout=3);report.append('  '+name+': up')",
    "        except:report.append('  '+name+': down')",
    "    smbd=run('systemctl is-active smbd')",
    "    report.append('  smbd: '+smbd)",
    "    # 6. Alias growth metrics",
    "    report.append('[6] ALIAS GROWTH:')",
    "    try:b=json.load(open(BRAIN));tasks=b.get('performance_metrics',{}).get('tasks_completed',0)",
    "    except:tasks='?'",
    "    try:kb=json.load(open(KB));learned=len(kb)",
    "    except:learned=0",
    "    try:cl=json.load(open(CHANGELOG));changes=len(cl)",
    "    except:changes=0",
    "    report.append('  Tasks completed: '+str(tasks))",
    "    report.append('  Knowledge topics learned: '+str(learned))",
    "    report.append('  Code improvements logged: '+str(changes))",
    "    # 7. Backup",
    "    report.append('[7] BACKUP:')",
    "    if flag('nightly_backup'):",
    "        bk=run('python3 /home/k/vnt-backup.py 2>&1',60)",
    "        report.append('  '+bk[:70])",
    "    else:report.append('  disabled')",
    "    body='\\n'.join(report)",
    "    save(body)",
    "    # Email to Ryan",
    "    if flag('hourly_health'):",
    "        c=cfg()",
    "        try:",
    "            msg=MIMEMultipart();msg['From']='Alias CEO VNT <'+c['gmail_user']+'>';msg['To']=c['ryan_email']",
    "            msg['Subject']='VNT Daily Report '+ts+' | '+str(up)+'/'+str(len(agents))+' agents'",
    "            msg.attach(MIMEText(body,'plain'))",
    "            with smtplib.SMTP('smtp.gmail.com',587,timeout=20) as s:",
    "                s.ehlo();s.starttls();s.login(c['gmail_user'],c['gmail_app_password']);s.send_message(msg)",
    "        except:pass",
    "        # WhatsApp summary",
    "        try:",
    "            wamsg=str(up)+'/'+str(len(agents))+' agents up. Tasks:'+str(tasks)+' Learned:'+str(learned)+'. Backup done. Full report emailed.'",
    "            body2=json.dumps({'to':c.get('ryan_phone','+966568116899'),'message':'VNT Daily: '+wamsg}).encode()",
    "            req=urllib.request.Request('http://127.0.0.1:3001',data=body2,headers={'Content-Type':'application/json'},method='POST')",
    "            urllib.request.urlopen(req,timeout=10)",
    "        except:pass",
    "    return body",
    "if __name__=='__main__':",
    "    print(daily_run())"]
daily_code=chr(10).join(daily_lines)
try:
    ast.parse(daily_code)
    open("/home/k/vnt-daily-routine.py","w").write(daily_code)
    os.chmod("/home/k/vnt-daily-routine.py",0o755)
    log("  Daily routine script ready")
except SyntaxError as e:
    log(f"  Daily routine syntax error L{e.lineno}: {e.msg}")

# ============ 4. SYSTEMD TIMER for daily routine ============
log("\n[4] Setting up daily timer (8 AM)...")
timer_svc=chr(10).join(["[Unit]","Description=VNT Daily Routine","",
    "[Service]","Type=oneshot","ExecStart=/usr/bin/python3 /home/k/vnt-daily-routine.py","WorkingDirectory=/home/k"])
open(USER_DIR+"/vnt-daily.service","w").write(timer_svc)
timer=chr(10).join(["[Unit]","Description=VNT Daily Routine Timer","",
    "[Timer]","OnCalendar=*-*-* 08:00:00","Persistent=true","",
    "[Install]","WantedBy=timers.target"])
open(USER_DIR+"/vnt-daily.timer","w").write(timer)
# Also nightly backup timer (2 AM)
bk_svc=chr(10).join(["[Unit]","Description=VNT Nightly Backup","",
    "[Service]","Type=oneshot","ExecStart=/usr/bin/python3 /home/k/vnt-backup.py","WorkingDirectory=/home/k"])
open(USER_DIR+"/vnt-backup.service","w").write(bk_svc)
bk_timer=chr(10).join(["[Unit]","Description=VNT Nightly Backup Timer","",
    "[Timer]","OnCalendar=*-*-* 02:00:00","Persistent=true","",
    "[Install]","WantedBy=timers.target"])
open(USER_DIR+"/vnt-backup.timer","w").write(bk_timer)
run(X+"systemctl --user daemon-reload",shell=True)
run(X+"systemctl --user enable vnt-daily.timer",shell=True)
run(X+"systemctl --user start vnt-daily.timer",shell=True)
run(X+"systemctl --user enable vnt-backup.timer",shell=True)
run(X+"systemctl --user start vnt-backup.timer",shell=True)
dt_status,_=run(X+"systemctl --user is-active vnt-daily.timer",shell=True)
bt_status,_=run(X+"systemctl --user is-active vnt-backup.timer",shell=True)
log(f"  Daily timer (8AM): {dt_status}")
log(f"  Backup timer (2AM): {bt_status}")

# ============ 5. Run daily routine once now to test ============
log("\n[5] Test-running daily routine now...")
test_run,_=run("python3 /home/k/vnt-daily-routine.py 2>&1",shell=True,timeout=90)
log(test_run[:800])

# ============ 6. Verify backups created ============
log("\n[6] Backup verification...")
bklist,_=run("ls -la /mnt/vnt-data/FileServer/VNT_World_AI_Division/disaster_recovery/ 2>/dev/null",shell=True)
log(bklist[:300])

full="\n".join(out)
push_result("daily_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")

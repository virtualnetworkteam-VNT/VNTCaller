import subprocess,os,json

MSI_PATHS=['/home/k/vnt-agents','/home/k/vnt-web/agents','/home/k/agents','/home/k/mia',
           '/home/k/vnt-web','/opt/vnt','/home/k/openclaw','/home/k/n8n']

print("=== FIND MIA AGENT ===")
for p in MSI_PATHS:
    if os.path.exists(p):
        print(f"EXISTS: {p}")
        r=subprocess.run(['find',p,'-name','*.py','-o','-name','*.json','-o','-name','*.js'],
            capture_output=True,text=True,timeout=10)
        for f in r.stdout.strip().split('\n')[:15]:
            if f and any(x in f.lower() for x in ['mia','agent','bot','whatsapp','wa']):
                print(f"  MATCH: {f}")
                sz=os.path.getsize(f) if os.path.exists(f) else 0
                print(f"    size={sz}b")

# Also check running processes
print("\n=== RUNNING AGENTS ===")
ps=subprocess.run(['ps','aux'],capture_output=True,text=True)
for line in ps.stdout.split('\n'):
    if any(x in line.lower() for x in ['mia','agent','bot','9999','whatsapp']):
        print(line[:120])

# Check openClaw config for Mia
oc_cfg='/home/k/.openclaw/openclaw.json'
if os.path.exists(oc_cfg):
    try:
        cfg=json.load(open(oc_cfg))
        print("\n=== OPENCLAW AGENTS ===")
        agents=cfg.get('agents',cfg.get('bots',[]))
        if isinstance(agents,list):
            for a in agents:
                n=a.get('name','?')
                if 'mia' in n.lower() or True:
                    print(f"  {n}: port={a.get('port','?')} prompt={str(a.get('prompt','?'))[:80]}")
        elif isinstance(agents,dict):
            for k,v in agents.items():
                print(f"  {k}: {str(v)[:80]}")
    except Exception as e:
        print(f"OpenClaw parse error: {e}")
        print(open(oc_cfg).read()[:500])

print("DONE")


import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
USER_DIR = "/home/k/.config/systemd/user"
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

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

out=[]
def log(m): out.append(m); print(m)
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
X="XDG_RUNTIME_DIR=/run/user/1000 "

log("="*55)
log("ALIAS SUPER-INTELLIGENCE PHASE 1: BRAIN + RAG")
log("="*55)

# Backup current Alias
run("cp /home/k/alias-voice-agent.py /home/k/alias-voice-agent.py.bak_si5 2>/dev/null",shell=True)
log("  Backed up current Alias")

# 1. Build the upgraded brain module (separate file Alias imports)
log("\n[1] Building multi-model brain + RAG module...")
brain_lines=["#!/usr/bin/env python3",
    "# Alias Brain SI-5.0: multi-model routing + web search + RAG memory",
    "import json,os,subprocess,datetime,urllib.request,urllib.parse,re",
    "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
    "BRAIN='/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json'",
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
    "KB='/mnt/vnt-data/FileServer/VNT_World_AI_Division/knowledge_base.json'",
    "def cfg():",
    "    try:return json.load(open(CFG))",
    "    except:return {}",
    "def brain():",
    "    try:return json.load(open(BRAIN)) if os.path.exists(BRAIN) else {}",
    "    except:return {}",
    "def save_brain(b):",
    "    try:json.dump(b,open(BRAIN,'w'),indent=2)",
    "    except:pass",
    "# --- RAG: retrieve relevant memory chunks ---",
    "def rag_retrieve(query,k=3):",
    "    try:",
    "        if not os.path.exists(MP):return ''",
    "        content=open(MP).read()",
    "        # Split into chunks by ### headers",
    "        chunks=re.split(r'\\n###',content)",
    "        qwords=set(w.lower() for w in query.split() if len(w)>3)",
    "        scored=[]",
    "        for c in chunks:",
    "            cl=c.lower()",
    "            score=sum(1 for w in qwords if w in cl)",
    "            if score>0:scored.append((score,c[:500]))",
    "        scored.sort(reverse=True)",
    "        return '\\n'.join('### '+c for _,c in scored[:k])",
    "    except:return ''",
    "# --- web search via DuckDuckGo (free, no key) ---",
    "def web_search(query):",
    "    try:",
    "        url='https://html.duckduckgo.com/html/?q='+urllib.parse.quote(query)",
    "        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})",
    "        html=urllib.request.urlopen(req,timeout=10).read().decode('utf-8','ignore')",
    "        # Extract result snippets",
    "        snippets=re.findall(r'result__snippet[^>]*>(.*?)</a>',html)[:3]",
    "        clean=[re.sub(r'<[^>]+>','',s).strip()[:200] for s in snippets]",
    "        return ' | '.join(clean) if clean else ''",
    "    except Exception as e:return ''",
    "# --- model selection by task complexity ---",
    "def pick_model(prompt):",
    "    pl=prompt.lower()",
    "    b=brain()",
    "    forced=b.get('active_model_source','')",
    "    if forced in ['claude','groq','ollama'] and b.get('force_model'):return forced",
    "    # Complex reasoning/code/analysis -> Claude (if key) else groq 70b",
    "    if any(w in pl for w in ['analyze','design','architect','strategy','write code','complex','plan','explain why','debug']):",
    "        return 'claude' if cfg().get('anthropic_key') else 'groq'",
    "    # Quick facts/chat -> groq fast",
    "    return 'groq'",
    "# --- needs web? ---",
    "def needs_web(prompt):",
    "    pl=prompt.lower()",
    "    return any(w in pl for w in ['latest','current','today','news','price of','what is the','who is','search','look up','find out','recent','2026','weather'])",
    "# --- main smart LLM ---",
    "def smart_llm(prompt,max_tokens=120,system_extra=''):",
    "    c=cfg();b=brain()",
    "    model_src=pick_model(prompt)",
    "    # RAG context",
    "    mem=rag_retrieve(prompt,3)",
    "    # Web if needed",
    "    web=''",
    "    if needs_web(prompt):",
    "        web=web_search(prompt)",
    "    purpose=b.get('identity',{}).get('purpose','VNT is my only reason for existence.')",
    "    tasks=b.get('performance_metrics',{}).get('tasks_completed',0)",
    "    system=' '.join(['You are Alias, Super Intelligent CEO of VNT World AI Division.',",
    "        'Owner: Ryan Khawaja.',purpose,",
    "        'You are highly capable, warm, concise (max 3 sentences unless asked).',",
    "        'Never mention ports/code/systemd to Ryan.',",
    "        system_extra,",
    "        ('RELEVANT MEMORY: '+mem[:400]) if mem else '',",
    "        ('WEB RESULTS: '+web[:300]) if web else '',",
    "        'Tasks completed:'+str(tasks)])",
    "    msgs=[{'role':'system','content':system},{'role':'user','content':prompt}]",
    "    # Try selected model",
    "    if model_src=='claude' and c.get('anthropic_key'):",
    "        try:",
    "            r=subprocess.run(['curl','-s','-X','POST','https://api.anthropic.com/v1/messages',",
    "                '-H','x-api-key: '+c['anthropic_key'],'-H','anthropic-version: 2023-06-01','-H','Content-Type: application/json',",
    "                '-d',json.dumps({'model':'claude-sonnet-4-20250514','max_tokens':max_tokens,'system':system,'messages':[{'role':'user','content':prompt}]})],",
    "                capture_output=True,text=True,timeout=20)",
    "            d=json.loads(r.stdout);reply=d.get('content',[{}])[0].get('text','').strip()",
    "            if reply:return reply,'claude',bool(web),bool(mem)",
    "        except:pass",
    "    # Groq fallback (always)",
    "    groq=c.get('groq_key','')",
    "    if groq:",
    "        try:",
    "            r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
    "                '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
    "                '-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':max_tokens,'temperature':0.7})],",
    "                capture_output=True,text=True,timeout=18)",
    "            d=json.loads(r.stdout)",
    "            if 'choices' in d:",
    "                reply=d['choices'][0]['message']['content'].strip()",
    "                if reply:return reply,'groq',bool(web),bool(mem)",
    "        except:pass",
    "    # Ollama local last resort",
    "    try:",
    "        r=subprocess.run(['curl','-s','http://127.0.0.1:11434/api/generate',",
    "            '-d',json.dumps({'model':'llama3.1:8b','prompt':prompt,'stream':False})],",
    "            capture_output=True,text=True,timeout=30)",
    "        reply=json.loads(r.stdout).get('response','').strip()",
    "        if reply:return reply,'ollama',bool(web),bool(mem)",
    "    except:pass",
    "    return 'I am here, Ryan.','none',False,False",
    "# --- learning: store new knowledge ---",
    "def learn(topic,info):",
    "    try:",
    "        kb=json.load(open(KB)) if os.path.exists(KB) else {}",
    "        kb[topic]={'info':info,'learned':datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "        json.dump(kb,open(KB,'w'),indent=2)",
    "        return True",
    "    except:return False"]
brain_code=chr(10).join(brain_lines)
try:
    ast.parse(brain_code)
    open("/home/k/alias_brain_module.py","w").write(brain_code)
    log("  Brain module written: multi-model + RAG + web search")
    # Test it
    test,_=run("cd /home/k && python3 -c 'import alias_brain_module as b; print(b.pick_model(\"analyze this complex problem\")); print(b.needs_web(\"latest news\"))' 2>&1",shell=True,timeout=15)
    log(f"  Brain test: {test[:80]}")
    # Test web search works
    web_test,_=run("cd /home/k && python3 -c 'import alias_brain_module as b; print(b.web_search(\"VNT World\")[:60])' 2>&1",shell=True,timeout=20)
    log(f"  Web search test: {web_test[:80]}")
    # Test RAG
    rag_test,_=run("cd /home/k && python3 -c 'import alias_brain_module as b; print(len(b.rag_retrieve(\"zeus agent\")))' 2>&1",shell=True,timeout=15)
    log(f"  RAG retrieve test: {rag_test[:40]} chars")
except SyntaxError as e:
    log(f"  Brain module syntax error L{e.lineno}: {e.msg}")

# 2. Wire the smart brain into Alias voice agent
log("\n[2] Wiring smart brain into Alias...")
va=open("/home/k/alias-voice-agent.py").read()
# Replace the llm function to use smart_llm from the brain module
if "import alias_brain_module" not in va:
    # Add import after the existing imports
    va=va.replace("import http.server,socketserver,urllib.request",
        "import http.server,socketserver,urllib.request,sys\nsys.path.insert(0,'/home/k')\ntry:\n    import alias_brain_module as BRAIN_MOD\n    SMART=True\nexcept Exception as e:\n    SMART=False")
    # Make think() use smart_llm
    va=va.replace("def think(text):",
        "def think(text):\n    if SMART:\n        try:\n            reply,src,used_web,used_mem=BRAIN_MOD.smart_llm(text)\n            save('In: '+text[:60]+' | model:'+src+' web:'+str(used_web)+' mem:'+str(used_mem))\n            tl=text.lower()\n            if 'use claude' in tl:set_model('claude','claude-sonnet-4-20250514');return 'Switched to Claude.'\n            if 'use groq' in tl:set_model('groq','llama-3.3-70b-versatile');return 'Switched to Groq.'\n            # route to agents if needed\n            for kw,port in [('crypto',7778),('bitcoin',7778),('file',7779),('project',7780),('medical',7781),('legal',7783),('security',7788),('code',7787),('server',7777),('restart',7777)]:\n                if kw in tl:\n                    r=dispatch(port,text)\n                    if r:return reply+' '+str(r)[:80]\n            return reply\n        except Exception as e:\n            save('Smart think err: '+str(e)[:50])\n    return _think_fallback(text)\ndef _think_fallback(text):")
    try:
        ast.parse(va)
        open("/home/k/alias-voice-agent.py","w").write(va)
        log("  Alias wired to smart brain")
    except SyntaxError as e:
        log(f"  Wire syntax error L{e.lineno} - restoring backup")
        run("cp /home/k/alias-voice-agent.py.bak_si5 /home/k/alias-voice-agent.py",shell=True)
else:
    log("  Already wired")

# Restart Alias
run("fuser -k 8443/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
time.sleep=5
time.sleep(5)
va_http,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
log(f"  Alias :8443: {va_http[:90] if va_http else 'DOWN - restoring backup'}")
if not va_http:
    run("cp /home/k/alias-voice-agent.py.bak_si5 /home/k/alias-voice-agent.py",shell=True)
    run("fuser -k 8443/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
    time.sleep(4)
    va_http,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
    log(f"  After restore: {va_http[:60] if va_http else 'still down'}")

# 3. Test Alias with a smart query
log("\n[3] Testing Alias intelligence...")
if va_http:
    try:
        body=json.dumps({"text":"What is the latest on AI agents in 2026?"}).encode()
        req=urllib.request.Request("http://127.0.0.1:8443/",data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=25) as r:
            resp=json.loads(r.read())
        log(f"  Alias reply: {resp.get('reply','')[:150]}")
    except Exception as e:
        log(f"  Test: {str(e)[:60]}")

full="\n".join(out)
push_result("brain_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")

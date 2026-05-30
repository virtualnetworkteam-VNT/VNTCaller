
import subprocess,os,json,datetime,urllib.request

M4="192.168.10.94"
M4U="Alias"
TS=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def ssh(c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8",
        M4U+"@"+M4,c],capture_output=True,text=True,timeout=t)
    return r.stdout.strip(),r.stderr.strip()

def run(c,t=20,shell=False):
    r=subprocess.run(c,shell=shell,capture_output=True,text=True,timeout=t)
    return r.stdout.strip()

print("="*55)
print("FIX BROWSER ACCESS TO M4 API")
print(TS)
print("="*55)

# 1. Find web root
web_root=""
for d in ["/home/k/vnt-web","/home/k/public","/var/www/html"]:
    if os.path.isdir(d): web_root=d; break
if not web_root:
    os.makedirs("/home/k/vnt-web",exist_ok=True)
    web_root="/home/k/vnt-web"
print(f"Web root: {web_root}")

# 2. Check if API reachable from MSI (same network as browser)
print("\nChecking API reachability from MSI...")
try:
    with urllib.request.urlopen("http://"+M4+":3333/health",timeout=8) as r:
        d=json.loads(r.read())
        print(f"  FROM MSI: {json.dumps(d)[:80]}")
        reachable=True
except Exception as e:
    print(f"  FROM MSI: BLOCKED - {e}")
    reachable=False

# 3. If not reachable, fix M4 firewall
if not reachable:
    print("\nDisabling M4 firewall...")
    o,e=ssh("/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off")
    print(f"  Firewall: {o} {e}")
    # Check binding
    bind,_=ssh("lsof -i :3333 2>/dev/null | head -3")
    print(f"  Port binding: {bind}")
    import time; time.sleep(3)
    try:
        with urllib.request.urlopen("http://"+M4+":3333/health",timeout=8) as r:
            d=json.loads(r.read())
            print(f"  AFTER FIX: {json.dumps(d)[:80]}")
            reachable=True
    except Exception as e2:
        print(f"  STILL BLOCKED: {e2}")

# 4. Write correct media.html
print("\nWriting media.html...")
# Read CSS carefully - store in variable to avoid multiline issues in f-string
api_url="http://"+M4+":3333"
html_path=web_root+"/media.html"

html_parts=[
    '<!DOCTYPE html><html lang="en"><head>',
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
    '<title>VNT//MEDIA STUDIO</title>',
    '<style>',
    '*{margin:0;padding:0;box-sizing:border-box}',
    'body{background:#0a0a0f;color:#e0e0e0;font-family:Segoe UI,monospace;min-height:100vh}',
    '.top{background:#0d0d1a;border-bottom:1px solid #1a1a2e;padding:10px 20px;display:flex;justify-content:space-between;align-items:center}',
    '.brand{color:#00ffcc;font-size:14px;font-weight:700;letter-spacing:2px}',
    '.sbar{display:flex;gap:16px;font-size:11px;align-items:center}',
    '.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}',
    '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1px;background:#1a1a2e}',
    '.panel{background:#0d0d1a;padding:18px}',
    '.pt{font-size:10px;letter-spacing:3px;color:#555;text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:8px}',
    '.badge{background:#1a1a2e;color:#888;font-size:9px;padding:2px 6px;border-radius:3px;border:1px solid #333}',
    '.badge.on{color:#00ffcc;border-color:#00ffcc}',
    '.badge.warn{color:#ff8800;border-color:#ff8800}',
    'textarea{width:100%;background:#050508;border:1px solid #1a1a2e;color:#c0ffc0;padding:8px;border-radius:4px;resize:vertical;font-size:12px;min-height:65px}',
    'textarea:focus{outline:none;border-color:#00ffcc}',
    'input[type=range]{width:100%;accent-color:#00ffcc;margin:3px 0}',
    'select{width:100%;background:#050508;border:1px solid #1a1a2e;color:#c0ffc0;padding:7px;border-radius:4px;font-size:12px}',
    '.lbl{font-size:10px;color:#555;margin:7px 0 2px;letter-spacing:1px}',
    '.btn{width:100%;padding:11px;border:none;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:2px;cursor:pointer;margin-top:10px}',
    '.bi{background:#00ddff;color:#000}',
    '.bv{background:#aa00ff;color:#fff}',
    '.b3{background:#ffaa00;color:#000}',
    '.ba{background:#dd44ff;color:#fff}',
    '.b2{background:#ff6600;color:#fff}',
    '.btn:disabled{opacity:.4;cursor:not-allowed}',
    '.out{margin-top:12px;min-height:55px;display:flex;align-items:center;justify-content:center;background:#050508;border:1px solid #1a1a2e;border-radius:4px;overflow:hidden;padding:4px}',
    '.out img,.out video,.out audio{max-width:100%;max-height:220px}',
    '.lg{font-size:10px;color:#ff4444;margin-top:5px;min-height:14px;font-family:monospace}',
    '.lg.ok{color:#00ff88}',
    '.fp{grid-column:1/-1}',
    '</style></head><body>',
    '<div class="top">',
    '  <div class="brand">VNT//MEDIA STUDIO</div>',
    '  <div class="sbar">',
    '    <span><span class="dot" id="ad" style="background:#ff8800"></span><span id="at">Connecting...</span></span>',
    '    <span><span class="dot" id="cd" style="background:#888"></span>ComfyUI</span>',
    '    <a href="http://'+M4+':7861" target="_blank" style="color:#555;font-size:11px">ComfyUI UI</a>',
    '  </div>',
    '</div>',
    '<div class="grid">',
    # Image panel
    '<div class="panel">',
    '  <div class="pt">&#9670; IMAGE GENERATION <span class="badge on">SD 1.5</span></div>',
    '  <div class="lbl">PROMPT</div>',
    '  <textarea id="ip">a photorealistic eagle in flight, sharp feathers, 8k uhd</textarea>',
    '  <div class="lbl">NEGATIVE PROMPT</div>',
    '  <textarea id="in" rows="2">blurry, watermark, low quality</textarea>',
    '  <div class="lbl">WIDTH</div><select id="iw"><option>256</option><option selected>512</option><option>768</option><option>1024</option></select>',
    '  <div class="lbl">HEIGHT</div><select id="ih"><option>256</option><option selected>512</option><option>768</option><option>1024</option></select>',
    '  <div class="lbl">STEPS &mdash; <span id="sv">25</span></div>',
    '  <input type="range" id="ss" min="10" max="50" value="25" oninput="sv.textContent=this.value">',
    '  <button class="btn bi" id="bi" onclick="genImg()">&#9654; GENERATE IMAGE</button>',
    '  <div class="out" id="io"><span style="color:#333;font-size:11px">output here</span></div>',
    '  <div class="lg" id="il"></div>',
    '</div>',
    # Video panel
    '<div class="panel">',
    '  <div class="pt">&#9670; VIDEO GENERATION <span class="badge warn">DREAMLIKE</span></div>',
    '  <div class="lbl">PROMPT</div>',
    '  <textarea id="vp">bird side of a lake, cinematic smooth motion</textarea>',
    '  <div class="lbl">FRAMES</div><select id="vf"><option>4</option><option>6</option><option selected>8</option><option>12</option><option>16</option></select>',
    '  <div class="lbl">FPS</div><select id="vr"><option>4</option><option>6</option><option selected>8</option><option>12</option></select>',
    '  <div class="lbl">STEPS &mdash; <span id="vs">15</span></div>',
    '  <input type="range" id="vi" min="5" max="30" value="15" oninput="vs.textContent=this.value">',
    '  <button class="btn bv" id="bv" onclick="genVid()">&#9654; GENERATE VIDEO</button>',
    '  <div class="out" id="vo"><span style="color:#333;font-size:11px">output here</span></div>',
    '  <div class="lg" id="vl"></div>',
    '</div>',
    # 3D panel
    '<div class="panel">',
    '  <div class="pt">&#9670; 3D GENERATION <span class="badge warn">TRIPOSR</span></div>',
    '  <div class="lbl">OBJECT DESCRIPTION</div>',
    '  <textarea id="dp">bird</textarea>',
    '  <div class="lbl">STEPS &mdash; <span id="ds">20</span></div>',
    '  <input type="range" id="di" min="10" max="64" value="20" oninput="ds.textContent=this.value">',
    '  <button class="btn b3" id="b3" onclick="gen3D()">&#9654; GENERATE 3D</button>',
    '  <div class="out" id="do"><span style="color:#333;font-size:11px">output here</span></div>',
    '  <div class="lg" id="dl"></div>',
    '</div>',
    # Audio panel
    '<div class="panel">',
    '  <div class="pt">&#9670; AUDIO / MUSIC <span class="badge">BARK/SAY</span></div>',
    '  <div class="lbl">PROMPT</div>',
    '  <textarea id="ap">Welcome to VNT World AI Division</textarea>',
    '  <div class="lbl">TYPE</div><select id="at2"><option value="speech">Speech (TTS)</option><option value="music">Music</option></select>',
    '  <button class="btn ba" id="ba" onclick="genAud()">&#9654; GENERATE AUDIO</button>',
    '  <div class="out" id="ao"><span style="color:#333;font-size:11px">output here</span></div>',
    '  <div class="lg" id="al"></div>',
    '</div>',
    # 2D panel
    '<div class="panel fp">',
    '  <div class="pt">&#9670; 2D DRAWING GENERATOR <span class="badge on">NOVA</span></div>',
    '  <textarea id="tp" rows="2">a small room blueprint</textarea>',
    '  <button class="btn b2" id="b2" onclick="gen2D()">GENERATE 2D DRAWING</button>',
    '  <div class="out" id="to"><span style="color:#333;font-size:11px">output here</span></div>',
    '  <div class="lg" id="tl"></div>',
    '</div>',
    '</div>',
    # JavaScript
    '<script>',
    f'const A="{api_url}";',
    'function lg(id,m,ok){const e=document.getElementById(id);if(e){e.textContent=m;e.className="lg"+(ok?" ok":"")}}',
    'function sb(id,d,t){const b=document.getElementById(id);if(b){b.disabled=d;if(t)b.textContent=t}}',
    'async function chk(){',
    '  try{',
    '    const r=await fetch(A+"/health",{signal:AbortSignal.timeout(5000)});',
    '    const d=await r.json();',
    '    if(d.status==="online"){',
    '      document.getElementById("ad").style.background="#00ff88";',
    '      document.getElementById("at").textContent="API online";',
    '      document.getElementById("at").style.color="#00ff88";',
    '      document.getElementById("cd").style.background=d.comfyui==="ok"?"#00ff88":"#ff8800";',
    '    }',
    '  }catch(e){',
    '    document.getElementById("ad").style.background="#ff4444";',
    '    document.getElementById("at").textContent="API offline - retrying";',
    '    document.getElementById("at").style.color="#ff4444";',
    '    setTimeout(chk,10000);',
    '  }',
    '}',
    'async function api(ep,data,ms=300000){',
    '  const c=new AbortController();',
    '  const t=setTimeout(()=>c.abort(),ms);',
    '  try{',
    '    const r=await fetch(A+ep,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data),signal:c.signal});',
    '    clearTimeout(t);return await r.json();',
    '  }catch(e){clearTimeout(t);throw e;}',
    '}',
    'async function genImg(){',
    '  sb("bi",true,"Generating...");lg("il","Generating image...");',
    '  try{',
    '    const d=await api("/generate",{prompt:ip.value,width:parseInt(iw.value),height:parseInt(ih.value),steps:parseInt(ss.value)},300000);',
    '    if(d.url||d.path){',
    '      const u=d.url||(A+"/file/"+d.path.split("/").pop());',
    '      io.innerHTML="<img src="+u+"?t="+Date.now()+">";',
    '      lg("il","Done: "+u,true);',
    '    }else lg("il","Error: "+JSON.stringify(d).slice(0,80));',
    '  }catch(e){lg("il","Error: "+e.message);}',
    '  sb("bi",false,"&#9654; GENERATE IMAGE");',
    '}',
    'async function genVid(){',
    '  sb("bv",true,"Generating (3-8min)...");lg("vl","Generating video...");',
    '  try{',
    '    const d=await api("/generate-video",{prompt:vp.value,frames:parseInt(vf.value),fps:parseInt(vr.value),steps:parseInt(vi.value)},600000);',
    '    if(d.url||d.path){',
    '      const u=d.url||(A+"/file/"+d.path.split("/").pop());',
    '      vo.innerHTML="<video src="+u+"?t="+Date.now()+" controls></video>";',
    '      lg("vl","Done: "+u,true);',
    '    }else lg("vl","Error: "+JSON.stringify(d).slice(0,80));',
    '  }catch(e){lg("vl","Error: "+e.message);}',
    '  sb("bv",false,"&#9654; GENERATE VIDEO");',
    '}',
    'async function gen3D(){',
    '  sb("b3",true,"Generating (2-5min)...");lg("dl","Generating 3D model...");',
    '  try{',
    '    const d=await api("/generate-3d",{prompt:dp.value},300000);',
    '    let h="";',
    '    if(d.preview_url)h+="<img src="+d.preview_url+"?t="+Date.now()+" style=max-height:200px>";',
    '    if(d.gif_url)h+="<img src="+d.gif_url+"?t="+Date.now()+" style=max-height:200px>";',
    '    if(d.obj_url)h+="<br><a href="+d.obj_url+" style=color:#ffaa00;font-size:11px>Download OBJ</a>";',
    '    if(h){do.innerHTML=h;lg("dl","Done!",true);}',
    '    else lg("dl",(d.info||d.status||JSON.stringify(d)).slice(0,100));',
    '  }catch(e){lg("dl","Error: "+e.message);}',
    '  sb("b3",false,"&#9654; GENERATE 3D");',
    '}',
    'async function genAud(){',
    '  sb("ba",true,"Generating...");lg("al","Generating audio...");',
    '  try{',
    '    const d=await api("/generate-audio",{text:ap.value,type:at2.value},120000);',
    '    if(d.url){ao.innerHTML="<audio src="+d.url+"?t="+Date.now()+" controls style=width:100%></audio>";lg("al","Done: "+d.url,true);}',
    '    else lg("al","Error: "+JSON.stringify(d).slice(0,80));',
    '  }catch(e){lg("al","Error: "+e.message);}',
    '  sb("ba",false,"&#9654; GENERATE AUDIO");',
    '}',
    'async function gen2D(){',
    '  sb("b2",true,"Drawing...");lg("tl","Generating...");',
    '  try{',
    '    const d=await api("/generate",{prompt:tp.value+", 2D architectural blueprint, technical illustration",width:512,height:512,steps:20},300000);',
    '    if(d.url||d.path){',
    '      const u=d.url||(A+"/file/"+d.path.split("/").pop());',
    '      to.innerHTML="<img src="+u+"?t="+Date.now()+">";',
    '      lg("tl","Done: "+u,true);',
    '    }else lg("tl","Error: "+JSON.stringify(d).slice(0,80));',
    '  }catch(e){lg("tl","Error: "+e.message);}',
    '  sb("b2",false,"GENERATE 2D DRAWING");',
    '}',
    'chk();',
    'setInterval(chk,30000);',
    '</script>',
    '</body></html>'
]
html = "
".join(html_parts)
open(html_path,"w").write(html)
print(f"  Written: {html_path} ({len(html)} bytes)")

open(MP,"a").write(f"\n### Media Dashboard Fixed [{TS}]\nmedia.html rewritten with API={api_url}\n")
print(f"\nDashboard: http://192.168.10.96:8888/media.html")
print(f"API: {api_url}/health")

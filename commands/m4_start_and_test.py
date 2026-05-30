import subprocess, json, time, os, datetime, urllib.request, base64, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

M4  = "192.168.10.94"
M4U = "Alias"
PY  = "/Users/alias/miniforge3/envs/vnt/bin/python"
GEN = "/Users/alias/vnt-studio/generated"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
TS  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

try:
    cfg=json.load(open(CFG))
    GMAIL=cfg["gmail_user"]; GPASS=cfg["gmail_app_password"]; RYAN=cfg["ryan_email"]
except:
    GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"

def save(e):
    open(MP,"a").write("\n### Studio ["+TS+"]\n"+e+"\n")

def ssh(c, t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8",
        "-o","BatchMode=yes",M4U+"@"+M4,c],capture_output=True,text=True,timeout=t)
    return r.stdout.strip(),r.stderr.strip()

def scp_to(local,remote,t=30):
    r=subprocess.run(["scp","-o","StrictHostKeyChecking=no",local,M4U+"@"+M4+":"+remote],
        capture_output=True,text=True,timeout=t)
    return r.returncode==0

def get(ep,t=15):
    try:
        with urllib.request.urlopen(f"http://{M4}:3333{ep}",timeout=t) as r:
            return json.loads(r.read()),None
    except Exception as e: return None,str(e)

def post(ep,data,t=300):
    try:
        body=json.dumps(data).encode()
        req=urllib.request.Request(f"http://{M4}:3333{ep}",data=body,
            headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=t) as r:
            return json.loads(r.read()),None
    except Exception as e: return None,str(e)

RESULTS={}
print("="*60)
print("VNT STUDIO - FULL A-Z TEST")
print(TS)
print("="*60)

# ── Phase 0: Ensure API running ──
print("\n[0] Checking API...")
h,e=get("/health",t=6)
online=h and h.get("status")=="online"
print(f"  Status: {'ONLINE' if online else 'OFFLINE'}")

if not online:
    print("  Killing old processes and restarting...")
    ssh("lsof -ti:3333 | xargs kill -9 2>/dev/null; sleep 2")
    ssh("pkill -f studio_api 2>/dev/null; sleep 1")
    ssh("mkdir -p /Users/alias/vnt-studio/generated")

    # Check if file exists
    fcheck,_=ssh("test -f /Users/alias/vnt-studio/studio_api.py && echo EXISTS || echo MISSING")
    print(f"  File: {fcheck}")

    if "MISSING" in fcheck:
        # Write a standalone minimal API that works
        # Write via a python file on MSI then scp
        api_code = open("/home/k/vnt-studio-api.py").read() if os.path.exists("/home/k/vnt-studio-api.py") else None
        if not api_code:
            # Create minimal working API
            mini = [
                "import http.server,json,os,subprocess,datetime,time",
                "PY='/Users/alias/miniforge3/envs/vnt/bin/python'",
                "GEN='/Users/alias/vnt-studio/generated'",
                "os.makedirs(GEN,exist_ok=True)",
                "def log(m): print('['+datetime.datetime.now().strftime('%H:%M:%S')+'] '+m,flush=True)",
                "class H(http.server.BaseHTTPRequestHandler):",
                "    def log_message(self,*a): pass",
                "    def cors(self):",
                "        self.send_header('Access-Control-Allow-Origin','*')",
                "        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')",
                "        self.send_header('Access-Control-Allow-Headers','Content-Type')",
                "    def send_json(self,d,c=200):",
                "        b=json.dumps(d).encode()",
                "        self.send_response(c)",
                "        self.send_header('Content-Type','application/json')",
                "        self.cors()",
                "        self.send_header('Content-Length',str(len(b)))",
                "        self.end_headers()",
                "        self.wfile.write(b)",
                "    def do_OPTIONS(self):",
                "        self.send_response(200);self.cors();self.end_headers()",
                "    def do_GET(self):",
                "        p=self.path",
                "        if '/health' in p:",
                "            self.send_json({'status':'online','api':'VNT Studio v3.2','gen':GEN})",
                "        elif '/list' in p:",
                "            files=[{'name':f,'size':os.path.getsize(GEN+'/'+f),'url':'http://192.168.10.94:3333/file/'+f} for f in sorted(os.listdir(GEN)) if os.path.isfile(GEN+'/'+f)]",
                "            self.send_json({'files':files,'count':len(files)})",
                "        elif p.startswith('/file/'):",
                "            fp=GEN+'/'+p[6:]",
                "            if os.path.exists(fp):",
                "                ext=fp.split('.')[-1].lower()",
                "                ct={'png':'image/png','jpg':'image/jpeg','mp4':'video/mp4','gif':'image/gif','wav':'audio/wav','obj':'text/plain'}.get(ext,'application/octet-stream')",
                "                d=open(fp,'rb').read()",
                "                self.send_response(200)",
                "                self.send_header('Content-Type',ct)",
                "                self.send_header('Content-Length',str(len(d)))",
                "                self.cors();self.end_headers();self.wfile.write(d)",
                "            else: self.send_json({'error':'not found'},404)",
                "        else: self.send_json({'status':'online','version':'3.2'})",
                "    def do_POST(self):",
                "        n=int(self.headers.get('Content-Length',0))",
                "        try: body=json.loads(self.rfile.read(n)) if n else {}",
                "        except: body={}",
                "        ts=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')",
                "        log('POST '+self.path+' prompt='+str(body.get('prompt',''))[:40])",
                "        p=self.path",
                "        if '/generate-video' in p:",
                "            prompt=body.get('prompt','cinematic birds')",
                "            frames=int(body.get('frames',8)); fps=int(body.get('fps',8)); steps=int(body.get('steps',15))",
                "            out=GEN+'/video_'+ts+'.mp4'",
                "            sc='import torch,os,subprocess,numpy as np\\nfrom PIL import Image\\nfrom diffusers import StableDiffusionPipeline\\ndevice=\"mps\" if torch.backends.mps.is_available() else \"cpu\"\\ndtype=torch.float16 if device==\"mps\" else torch.float32\\npipe=StableDiffusionPipeline.from_pretrained(\"runwayml/stable-diffusion-v1-5\",torch_dtype=dtype,safety_checker=None)\\npipe=pipe.to(device);pipe.enable_attention_slicing()\\nprompt=\"'+prompt.replace('\"',\\'\\').replace(chr(10),' ')+', cinematic quality\"\\nneg=\"blurry,inconsistent,low quality\"\\nimgs=[]\\nfor i in range(4):\\n    gen=torch.Generator(device=device).manual_seed(42+i*13)\\n    imgs.append(pipe(prompt,negative_prompt=neg,num_inference_steps='+str(steps)+',width=512,height=288,generator=gen).images[0])\\nall_f=[]\\nfor i in range(len(imgs)-1):\\n    all_f.append(imgs[i])\\n    a=np.array(imgs[i]).astype(float);b=np.array(imgs[i+1]).astype(float)\\n    for j in range(1,3):\\n        t=j/3\\n        all_f.append(Image.fromarray(((1-t)*a+t*b).astype(np.uint8)))\\nall_f.append(imgs[-1]);all_f=all_f[:'+str(frames)+']\\nfd=\"'+out+'\".replace(\".mp4\",\"_f\");os.makedirs(fd,exist_ok=True)\\nfor i,f in enumerate(all_f): f.save(fd+f\"/f{i:04d}.png\")\\nsubprocess.run([\"ffmpeg\",\"-y\",\"-framerate\",\"'+str(fps)+'\",\"-i\",fd+\"/f%04d.png\",\"-c:v\",\"libx264\",\"-pix_fmt\",\"yuv420p\",\"-crf\",\"18\",\"-vf\",\"scale=512:288\",\"'+out+'\"],capture_output=True)\\nimport shutil;shutil.rmtree(fd,ignore_errors=True)\\nprint(\"SAVED\" if os.path.exists(\"'+out+'\") else \"FAILED\")'",
                "            r=subprocess.run([PY,'-c',sc],capture_output=True,text=True,timeout=600)",
                "            if os.path.exists(out): self.send_json({'status':'ok','path':out,'url':'http://192.168.10.94:3333/file/video_'+ts+'.mp4'})",
                "            else: self.send_json({'status':'error','stderr':r.stderr[-200:]})",
                "        elif '/generate-3d' in p:",
                "            prompt=body.get('prompt','a detailed bird')",
                "            od=GEN+'/3d_'+ts; os.makedirs(od,exist_ok=True)",
                "            sc='import sys,os\\ntry:\\n    from shap_e.diffusion.sample import sample_latents\\n    from shap_e.diffusion.gaussian_diffusion import diffusion_from_config\\n    from shap_e.models.download import load_model,load_config\\n    from shap_e.util.notebooks import create_pan_cameras,decode_latent_images,decode_latent_mesh\\n    from shap_e.util.image_util import linear_to_srgb\\n    from PIL import Image\\n    import torch,numpy as np\\n    dev=\"cpu\"\\n    xm=load_model(\"transmitter\",device=dev)\\n    model=load_model(\"text300M\",device=dev)\\n    diff=diffusion_from_config(load_config(\"diffusion\"))\\n    latents=sample_latents(batch_size=1,model=model,diffusion=diff,guidance_scale=15.0,model_kwargs=dict(texts=[\"'+prompt.replace('\"',\\'')+', detailed realistic\"]),progress=False,clip_denoised=True,use_fp16=False,use_karras=True,karras_steps=32,sigma_min=1e-3,sigma_max=160,s_churn=0)\\n    t=decode_latent_mesh(xm,latents[0]).tri_mesh()\\n    open(\"'+od+'/model.obj\",\"w\").write(\"\")\\n    with open(\"'+od+'/model.obj\",\"w\") as f: t.write_obj(f)\\n    cams=create_pan_cameras(128,dev)\\n    imgs=decode_latent_images(xm,latents[0],cams,rendering_mode=\"nerf\")\\n    frames=[(linear_to_srgb(img.detach().cpu().numpy())*255).astype(np.uint8) for img in imgs]\\n    pil_frames=[Image.fromarray(f) for f in frames]\\n    pil_frames[0].save(\"'+od+'/preview.png\")\\n    pil_frames[0].save(\"'+od+'/preview.gif\",save_all=True,append_images=pil_frames[1:],loop=0,duration=80)\\n    print(\"OK\")\\nexcept ImportError:\\n    import subprocess\\n    subprocess.run([sys.executable,\"-m\",\"pip\",\"install\",\"shap-e\",\"-q\"],capture_output=True)\\n    print(\"INSTALLING\")\\nexcept Exception as e:\\n    print(\"ERR:\"+str(e)[:200])'",
                "            r=subprocess.run([PY,'-c',sc],capture_output=True,text=True,timeout=300)",
                "            log('3D: '+r.stdout[-60:])",
                "            res={'status':'ok' if os.path.exists(od+'/model.obj') else 'generating','info':r.stdout[-80:]}",
                "            if os.path.exists(od+'/model.obj'): res['obj_url']='http://192.168.10.94:3333/file/3d_'+ts+'/model.obj'",
                "            if os.path.exists(od+'/preview.png'): res['preview_url']='http://192.168.10.94:3333/file/3d_'+ts+'/preview.png'",
                "            if os.path.exists(od+'/preview.gif'): res['gif_url']='http://192.168.10.94:3333/file/3d_'+ts+'/preview.gif'",
                "            self.send_json(res)",
                "        elif '/generate-audio' in p:",
                "            text=body.get('text',body.get('prompt','Hello from VNT'))",
                "            out=GEN+'/audio_'+ts+'.wav'",
                "            aiff=out.replace('.wav','.aiff')",
                "            subprocess.run(['say','-o',aiff,'--data-format=LEF32@22050',text],timeout=30)",
                "            subprocess.run(['ffmpeg','-y','-i',aiff,out],capture_output=True,timeout=15)",
                "            if not os.path.exists(out) and os.path.exists(aiff): os.rename(aiff,out)",
                "            if os.path.exists(out) and os.path.getsize(out)>100: self.send_json({'status':'ok','url':'http://192.168.10.94:3333/file/audio_'+ts+'.wav'})",
                "            else: self.send_json({'status':'error','error':'audio failed'})",
                "        elif '/generate' in p:",
                "            prompt=body.get('prompt','photorealistic bird')",
                "            w=min(int(body.get('width',512)),768); h=min(int(body.get('height',512)),768)",
                "            steps=int(body.get('steps',20)); out=GEN+'/img_'+ts+'.png'",
                "            enhanced=prompt+', 8k uhd, photorealistic, masterpiece, sharp focus'",
                "            neg='blurry,low quality,ugly,distorted,watermark'",
                "            sc='import torch,os\\nfrom diffusers import StableDiffusionPipeline\\ndevice=\"mps\" if torch.backends.mps.is_available() else \"cpu\"\\ndtype=torch.float16 if device==\"mps\" else torch.float32\\npipe=StableDiffusionPipeline.from_pretrained(\"runwayml/stable-diffusion-v1-5\",torch_dtype=dtype,safety_checker=None)\\npipe=pipe.to(device);pipe.enable_attention_slicing()\\nimg=pipe(\"'+enhanced.replace('\"',\\'')+'\",negative_prompt=\"'+neg+'\",num_inference_steps='+str(steps)+',width='+str(w)+',height='+str(h)+',guidance_scale=7.5).images[0]\\nimg.save(\"'+out+'\")\\nprint(\"SAVED\")'",
                "            r=subprocess.run([PY,'-c',sc],capture_output=True,text=True,timeout=300)",
                "            log('Image: '+r.stdout[-40:]+r.stderr[-40:])",
                "            if os.path.exists(out): self.send_json({'status':'ok','path':out,'url':'http://192.168.10.94:3333/file/img_'+ts+'.png'})",
                "            else: self.send_json({'status':'error','stderr':r.stderr[-300:]})",
                "        else: self.send_json({'error':'unknown: '+p},404)",
                "log('VNT Studio v3.2 on :3333')",
                "http.server.HTTPServer(('0.0.0.0',3333),H).serve_forever()",
            ]
            open("/tmp/studio_api_v3.py","w").write("\n".join(mini))
        scp_ok = scp_to("/tmp/studio_api_v3.py","/Users/alias/vnt-studio/studio_api.py")
        print(f"  SCP: {'OK' if scp_ok else 'FAILED'}")

    # Start API
    ssh(f"lsof -ti:3333 | xargs kill -9 2>/dev/null; sleep 1")
    ssh(f"nohup {PY} /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &")
    print("  Waiting 10s...")
    time.sleep(10)
    h,e=get("/health",t=8)
    online=h and h.get("status")=="online"
    if not online:
        log_o,_=ssh("tail -20 /tmp/studio.log")
        print(f"  Log:\n{log_o[:400]}")
        # Try python3
        ssh(f"lsof -ti:3333 | xargs kill -9 2>/dev/null; sleep 1")
        ssh("nohup python3 /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &")
        time.sleep(8)
        h,e=get("/health",t=8)
        online=h and h.get("status")=="online"
    print(f"  API: {'ONLINE' if online else 'OFFLINE'} - {json.dumps(h)[:80] if h else e}")

RESULTS["API_Health"]=("PASS",json.dumps(h)[:60] if h else str(e)) if online else ("FAIL","API could not start")

# ── Run all tests ──
if online:
    tests=[
        ("Image_Bird",    "/generate",{"prompt":"photorealistic eagle sharp 8k","width":512,"height":512,"steps":20},300),
        ("Image_Car",     "/generate",{"prompt":"Ferrari red sports car studio 8k photorealistic","width":512,"height":512,"steps":20},300),
        ("Image_Portrait","/generate",{"prompt":"professional business portrait studio lighting sharp 8k","width":512,"height":512,"steps":20},300),
        ("Video_Birds",   "/generate-video",{"prompt":"cinematic birds flying over lake sunset","frames":8,"fps":8,"steps":15},600),
        ("3D_Bird",       "/generate-3d",{"prompt":"realistic bird dove proper wings feathers anatomy"},300),
        ("Audio_Speech",  "/generate-audio",{"text":"Welcome to VNT World AI Division. All systems operational."},120),
    ]
    for name,ep,data,timeout in tests:
        print(f"\n  Testing {name}...")
        r,e=post(ep,data,timeout)
        if r and (r.get("status")=="ok" or r.get("obj_url") or r.get("preview_url")):
            url=r.get("url") or r.get("preview_url") or r.get("obj_url","")
            RESULTS[name]=("PASS",url[:80])
            print(f"    PASS: {url[:70]}")
        else:
            RESULTS[name]=("FAIL",str(e or r)[:80])
            print(f"    FAIL: {str(e or r)[:70]}")
        time.sleep(1)

    # File list
    fl,e=get("/list",t=10)
    if fl and "files" in fl:
        RESULTS["File_List"]=("PASS",f"{fl['count']} files")
        print(f"\n  File List: PASS ({fl['count']} files)")
    else:
        RESULTS["File_List"]=("FAIL",str(e))

else:
    for n in ["Image_Bird","Image_Car","Image_Portrait","Video_Birds","3D_Bird","Audio_Speech","File_List"]:
        RESULTS[n]=("FAIL","API offline")

# ── Summary ──
passed=sum(1 for v in RESULTS.values() if v[0]=="PASS")
total=len(RESULTS)

print(f"\n{'='*60}")
print(f"FINAL: {passed}/{total} TESTS PASSED")
for name,(status,detail) in RESULTS.items():
    icon="PASS" if status=="PASS" else "FAIL"
    print(f"  [{icon}] {name}: {detail[:60]}")

save(f"Studio A-Z Test {TS}: {passed}/{total} passed\n"+"\n".join(f"  {n}: {s} {d[:50]}" for n,(s,d) in RESULTS.items()))

# ── Email report with test images ──
try:
    msg=MIMEMultipart()
    msg["From"]=f"Alias CEO VNT <{GMAIL}>"
    msg["To"]=RYAN
    msg["Subject"]=f"Studio Test: {passed}/{total} Passed | A-Z Results | {TS}"
    lines=["VNT Media Studio - Full A-Z Test Report",f"Date: {TS}","",f"Score: {passed}/{total} tests passed",""]
    lines+=["TEST RESULTS:",""]
    for name,(status,detail) in RESULTS.items():
        lines.append(f"  [{status}] {name}")
        lines.append(f"         {detail[:80]}")
    lines+=["","Studio: http://"+M4+":3333/health","ComfyUI: http://"+M4+":7861","",
            "Regards,","Alias - CEO, VNT World AI Division"]
    msg.attach(MIMEText("\n".join(lines),"plain"))

    # Attach any generated images
    for fname in (os.listdir(GEN) if os.path.exists(GEN) else []):
        if fname.endswith(".png") and os.path.getsize(GEN+"/"+fname)<3*1024*1024:
            fpath=GEN+"/"+fname
            # SCP to MSI first
            local_path=f"/tmp/studio_{fname}"
            r=subprocess.run(["scp","-o","StrictHostKeyChecking=no",
                M4U+"@"+M4+":"+GEN+"/"+fname,local_path],
                capture_output=True,timeout=20)
            if r.returncode==0 and os.path.exists(local_path):
                with open(local_path,"rb") as f:
                    p=MIMEBase("application","octet-stream")
                    p.set_payload(f.read())
                encoders.encode_base64(p)
                p.add_header("Content-Disposition","attachment",filename=fname)
                msg.attach(p)

    with smtplib.SMTP("smtp.gmail.com",587,timeout=30) as s:
        s.ehlo();s.starttls();s.login(GMAIL,GPASS);s.send_message(msg)
    print("\nEmail sent with test images attached")
except Exception as e:
    print(f"Email error: {str(e)[:80]}")

print("="*60)

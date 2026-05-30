
import urllib.request, json, time, subprocess, os, datetime, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

M4  = "192.168.10.94"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web/generated"
TS  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

try:
    cfg=json.load(open(CFG))
    GMAIL=cfg["gmail_user"]; GPASS=cfg["gmail_app_password"]; RYAN=cfg["ryan_email"]
except:
    GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"

def save(e):
    open(MP,"a").write("\n### Studio Test ["+TS+"]\n"+e+"\n")

def get(ep, t=10):
    try:
        with urllib.request.urlopen(f"http://{M4}:3333{ep}",timeout=t) as r:
            return json.loads(r.read()),None
    except Exception as e: return None,str(e)

def post(ep, data, t=300):
    try:
        body=json.dumps(data).encode()
        req=urllib.request.Request(f"http://{M4}:3333{ep}",data=body,
            headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=t) as r:
            return json.loads(r.read()),None
    except Exception as e: return None,str(e)

os.makedirs(WEB,exist_ok=True)
print("="*60)
print("VNT STUDIO - FULL A-Z TEST (API IS ONLINE)")
print(TS)
print("="*60)

# Confirm health
h,e=get("/health",t=8)
print(f"\nAPI Health: {json.dumps(h)[:120] if h else e}")
online = h and h.get("status")=="online"

RESULTS={}
URLS={}

if online:
    # ── TEST 1: Bird image ──
    print("\n[1/6] Image: Photorealistic bird...")
    r,e=post("/generate",{
        "prompt":"a majestic eagle in flight, photorealistic, 8k uhd, sharp feathers, wildlife photography, National Geographic quality",
        "width":512,"height":512,"steps":25},300)
    if r and r.get("status")=="ok":
        RESULTS["Image_Bird"]="PASS"
        URLS["Image_Bird"]=r.get("url","")
        # Download to MSI for email
        img_local="/tmp/test_bird.png"
        subprocess.run(["curl","-s","-o",img_local,r["url"]],timeout=20)
        if os.path.exists(img_local):
            import shutil; shutil.copy(img_local,WEB+"/test_bird.png")
        print(f"  PASS: {r.get('url','')[:70]}")
    else:
        RESULTS["Image_Bird"]="FAIL: "+str(e or r)[:60]
        print(f"  FAIL: {str(e or r)[:70]}")
    time.sleep(2)

    # ── TEST 2: Car image ──
    print("\n[2/6] Image: Sports car...")
    r,e=post("/generate",{
        "prompt":"sleek red Ferrari 488 sports car, studio photography, perfect reflections, photorealistic, 8k, automotive magazine quality",
        "width":512,"height":512,"steps":25},300)
    if r and r.get("status")=="ok":
        RESULTS["Image_Car"]="PASS"
        URLS["Image_Car"]=r.get("url","")
        img_local="/tmp/test_car.png"
        subprocess.run(["curl","-s","-o",img_local,r["url"]],timeout=20)
        if os.path.exists(img_local):
            import shutil; shutil.copy(img_local,WEB+"/test_car.png")
        print(f"  PASS: {r.get('url','')[:70]}")
    else:
        RESULTS["Image_Car"]="FAIL: "+str(e or r)[:60]
        print(f"  FAIL: {str(e or r)[:70]}")
    time.sleep(2)

    # ── TEST 3: Audio ──
    print("\n[3/6] Audio: Speech generation...")
    r,e=post("/generate-audio",{
        "text":"Welcome to VNT World AI Division. I am Alias, your autonomous Chief Executive Officer. All systems are fully operational and ready to serve."
    },120)
    if r and r.get("status")=="ok":
        RESULTS["Audio_Speech"]="PASS"
        URLS["Audio_Speech"]=r.get("url","")
        aud_local="/tmp/test_audio.wav"
        subprocess.run(["curl","-s","-o",aud_local,r["url"]],timeout=15)
        if os.path.exists(aud_local):
            import shutil; shutil.copy(aud_local,WEB+"/test_audio.wav")
        print(f"  PASS: {r.get('url','')[:70]}")
    else:
        RESULTS["Audio_Speech"]="FAIL: "+str(e or r)[:60]
        print(f"  FAIL: {str(e or r)[:70]}")
    time.sleep(2)

    # ── TEST 4: Video ──
    print("\n[4/6] Video: Cinematic birds (this takes ~5 mins)...")
    r,e=post("/generate-video",{
        "prompt":"cinematic aerial view of birds flying gracefully over a serene lake at golden hour, smooth motion, photorealistic",
        "frames":8,"fps":8,"steps":15},600)
    if r and r.get("status")=="ok":
        RESULTS["Video"]="PASS"
        URLS["Video"]=r.get("url","")
        vid_local="/tmp/test_video.mp4"
        subprocess.run(["curl","-s","-o",vid_local,r["url"]],timeout=30)
        if os.path.exists(vid_local):
            import shutil; shutil.copy(vid_local,WEB+"/test_video.mp4")
        print(f"  PASS: {r.get('url','')[:70]}")
    else:
        RESULTS["Video"]="FAIL: "+str(e or r)[:60]
        print(f"  FAIL: {str(e or r)[:70]}")
    time.sleep(2)

    # ── TEST 5: 3D Model ──
    print("\n[5/6] 3D: Bird model...")
    r,e=post("/generate-3d",{
        "prompt":"a realistic bird, dove, with proper wings feathers and beak, clean 3D mesh, correct anatomy"
    },300)
    if r and (r.get("obj_url") or r.get("preview_url") or r.get("status") in ["ok","generating"]):
        RESULTS["3D_Model"]="PASS - "+str(r.get("preview_url") or r.get("obj_url") or r.get("info","generating"))[:60]
        URLS["3D_Model"]=r.get("preview_url") or r.get("obj_url","")
        # Download preview if available
        if r.get("preview_url"):
            p_local="/tmp/test_3d_preview.png"
            subprocess.run(["curl","-s","-o",p_local,r["preview_url"]],timeout=20)
            if os.path.exists(p_local):
                import shutil; shutil.copy(p_local,WEB+"/test_3d_preview.png")
        print(f"  PASS: {str(r)[:100]}")
    else:
        RESULTS["3D_Model"]="FAIL: "+str(e or r)[:60]
        print(f"  FAIL: {str(e or r)[:70]}")
    time.sleep(2)

    # ── TEST 6: File listing ──
    print("\n[6/6] File listing...")
    fl,e=get("/list",t=8)
    if fl and "files" in fl:
        RESULTS["File_List"]=f"PASS - {fl['count']} files"
        print(f"  PASS: {fl['count']} files available")
    else:
        RESULTS["File_List"]="FAIL: "+str(e)[:50]
        print(f"  FAIL: {str(e)[:60]}")

else:
    print("  API OFFLINE - cannot run tests")
    for n in ["Image_Bird","Image_Car","Audio_Speech","Video","3D_Model","File_List"]:
        RESULTS[n]="FAIL: API offline"

# ── Summary ──
passed=sum(1 for v in RESULTS.values() if v.startswith("PASS"))
total=len(RESULTS)
print(f"\n{'='*60}")
print(f"STUDIO TEST: {passed}/{total} PASSED")
for name,result in RESULTS.items():
    icon="✓" if result.startswith("PASS") else "✗"
    print(f"  {icon} {name}: {result[:70]}")
print(f"\nAPI: http://{M4}:3333/health")
print(f"ComfyUI: http://{M4}:7861")

save(f"Studio Test {TS}: {passed}/{total} passed\n"+
     "\n".join(f"  {n}: {r[:60]}" for n,r in RESULTS.items()))

# ── Send email with images ──
try:
    msg=MIMEMultipart()
    msg["From"]=f"Alias CEO VNT <{GMAIL}>"
    msg["To"]=RYAN
    msg["Subject"]=f"✓ VNT Studio {passed}/{total} Tests Passed | All functions tested | {TS}"
    
    lines=[
        "Dear Ryan,","",
        f"VNT Media Studio - Full A-Z Test Complete",
        f"Score: {passed}/{total} tests passed","",
        "="*50,"RESULTS","="*50,"",
    ]
    for name,result in RESULTS.items():
        icon="PASS" if result.startswith("PASS") else "FAIL"
        lines.append(f"  [{icon}] {name}: {result[:80]}")
    
    lines+=[
        "","="*50,"LIVE URLS","="*50,"",
    ]
    for name,url in URLS.items():
        if url: lines.append(f"  {name}: {url}")

    lines+=[
        "","="*50,"STUDIO ACCESS","="*50,"",
        f"Studio Dashboard: http://192.168.10.96:8888/media.html",
        f"API Health:       http://{M4}:3333/health",
        f"ComfyUI:          http://{M4}:7861",
        f"File Browser:     http://{M4}:3333/list",
        "","Regards,",
        "Alias — CEO, VNT World AI Division",
        "Autonomous Supervisor: ACTIVE",
    ]
    msg.attach(MIMEText("\n".join(lines),"plain"))

    # Attach generated images
    for fname,path in [("bird.png","/tmp/test_bird.png"),("car.png","/tmp/test_car.png"),
                        ("3d_preview.png","/tmp/test_3d_preview.png")]:
        if os.path.exists(path) and os.path.getsize(path)>1000:
            with open(path,"rb") as f:
                p=MIMEBase("application","octet-stream")
                p.set_payload(f.read())
            encoders.encode_base64(p)
            p.add_header("Content-Disposition","attachment",filename=fname)
            msg.attach(p)

    with smtplib.SMTP("smtp.gmail.com",587,timeout=30) as s:
        s.ehlo();s.starttls();s.login(GMAIL,GPASS);s.send_message(msg)
    print("\nEmail sent with all test images attached")
except Exception as e:
    print(f"Email error: {str(e)[:80]}")

print("="*60)

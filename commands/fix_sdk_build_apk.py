
import subprocess, os, time, datetime, shutil

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
APP_DIR = "/home/k/hannahbird-app"
REDMI_IP = "192.168.10.191"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### HannahBird APK ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

def run(cmd, cwd=None, timeout=300):
    r=subprocess.run(cmd,shell=True,capture_output=True,text=True,cwd=cwd,timeout=timeout)
    out=(r.stdout+r.stderr)[-600:]
    if out.strip(): print(out)
    return r.returncode==0

# Step 1: Find Android SDK location
print("=== Finding Android SDK ===")
sdk=None
candidates=[
    os.environ.get("ANDROID_HOME",""),
    os.path.expanduser("~/Android/Sdk"),
    "/opt/android-sdk",
    "/home/k/android-sdk",
]
# Also check VNTCaller project
r=subprocess.run(["find","/home/k","-name","local.properties","-maxdepth","5"],
    capture_output=True,text=True)
for lp in r.stdout.strip().split(chr(10)):
    if lp and os.path.exists(lp):
        content=open(lp).read()
        if "sdk.dir" in content:
            for line in content.split(chr(10)):
                if line.startswith("sdk.dir="):
                    p=line.split("=",1)[1].strip()
                    if os.path.exists(p):
                        sdk=p
                        print("SDK from existing local.properties:", sdk)
                        break

if not sdk:
    for p in candidates:
        if p and os.path.exists(str(p)+"/build-tools"):
            sdk=p; break

if not sdk:
    # Find by looking for adb or aapt
    r2=subprocess.run(["find","/home","/opt","-name","aapt","-maxdepth","8","2>/dev/null"],
        shell=True,capture_output=True,text=True)
    if r2.stdout.strip():
        # SDK is 3 levels up from aapt (build-tools/version/aapt)
        aapt_path=r2.stdout.strip().split(chr(10))[0]
        sdk=os.path.dirname(os.path.dirname(os.path.dirname(aapt_path)))
        print("SDK via aapt:", sdk)

if not sdk:
    print("SDK not found. Installing minimal SDK...")
    sdk="/home/k/android-sdk"
    os.makedirs(sdk+"/cmdline-tools",exist_ok=True)
    run("wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/ct.zip",timeout=120)
    run("unzip -q /tmp/ct.zip -d "+sdk+"/cmdline-tools/")
    run("mv "+sdk+"/cmdline-tools/cmdline-tools "+sdk+"/cmdline-tools/latest 2>/dev/null || true")
    os.environ["ANDROID_HOME"]=sdk
    os.environ["PATH"]+="/home/k/android-sdk/cmdline-tools/latest/bin:/home/k/android-sdk/platform-tools"
    run('yes | '+sdk+'/cmdline-tools/latest/bin/sdkmanager --licenses 2>/dev/null || true',timeout=60)
    run(sdk+'/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"',timeout=600)

print("Using SDK:", sdk)

# Step 2: Write local.properties
lp_path=APP_DIR+"/android/local.properties"
open(lp_path,"w").write("sdk.dir="+str(sdk)+chr(10))
print("Written:", lp_path)
print("Content:", open(lp_path).read())

# Step 3: Update game HTML - mobile only, no keyboard, touch/swipe/tap
mobile_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#87CEEB">
<title>HannahBird.io</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{width:100%;height:100%;overflow:hidden;background:#87CEEB;touch-action:none;user-select:none}
canvas{position:fixed;top:0;left:0;display:block}
#hud{position:fixed;top:0;left:0;right:0;z-index:10;pointer-events:none}
#top{display:flex;justify-content:space-between;align-items:center;padding:env(safe-area-inset-top,8px) 12px 8px;background:rgba(0,0,0,0.45)}
#logo{font-size:20px;font-weight:900;color:#FFE66D;font-family:sans-serif}
#logo b{color:#7FFF7F}
.st{text-align:center;background:rgba(255,255,255,0.15);border-radius:10px;padding:3px 10px;border:2px solid rgba(255,255,255,0.3)}
.sn{font-size:18px;font-weight:900;color:#FFE66D;font-family:sans-serif}
.sl{font-size:8px;color:rgba(255,255,255,0.8);text-transform:uppercase;letter-spacing:0.5px}
#pb{height:8px;background:rgba(0,0,0,0.3);margin:2px 10px 0}
#pbf{height:100%;background:linear-gradient(90deg,#7FFF7F,#32CD32);border-radius:4px;transition:width .4s}
#screen{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(0,0,0,0.65);z-index:20}
#screen h1{font-size:min(48px,11vw);font-weight:900;color:#FFE66D;text-align:center;text-shadow:3px 3px 0 #8B6914;line-height:1.1;font-family:sans-serif}
#screen h1 b{color:#7FFF7F}
#screen p{color:#eee;font-size:15px;margin:10px 20px 24px;text-align:center;line-height:1.5}
.btn{background:linear-gradient(135deg,#FFE66D,#FFA500);color:#1a0a00;border:none;padding:16px 42px;font-size:20px;font-weight:900;border-radius:50px;cursor:pointer;font-family:sans-serif;box-shadow:0 5px 0 #8B6914;letter-spacing:0.5px;min-width:200px}
.btn:active{transform:translateY(3px);box-shadow:0 2px 0 #8B6914}
#boost{position:fixed;bottom:calc(env(safe-area-inset-bottom,0px) + 24px);left:24px;width:72px;height:72px;background:rgba(255,100,50,0.85);border:3px solid rgba(255,255,255,0.6);border-radius:50%;font-size:30px;cursor:pointer;pointer-events:all;z-index:10;display:none;align-items:center;justify-content:center;box-shadow:0 4px 0 rgba(0,0,0,0.4)}
#boost:active{transform:scale(0.92)}
#swipe-hint{position:fixed;bottom:calc(env(safe-area-inset-bottom,0px) + 30px);right:24px;background:rgba(0,0,0,0.5);border-radius:10px;padding:8px 14px;color:rgba(255,255,255,0.7);font-size:12px;pointer-events:none;z-index:10;display:none;text-align:center;line-height:1.4}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud" style="display:none">
  <div id="top">
    <div id="logo">Hannah<b>Bird</b>.io</div>
    <div class="st"><div class="sn" id="sn">1</div><div class="sl">Nests</div></div>
    <div class="st"><div class="sn" id="sp">0%</div><div class="sl">Territory</div></div>
    <div class="st"><div class="sn" id="se">0</div><div class="sl">Rivals</div></div>
  </div>
  <div id="pb"><div id="pbf" style="width:2%"></div></div>
</div>
<div id="screen">
  <h1>Hannah<b>Bird</b>.io 🐦</h1>
  <p>Swipe to fly · Capture nests<br>Grow your flock · Rule the sky! 🌳</p>
  <button class="btn" id="sb">🐦  Let's Fly!</button>
  <p style="color:rgba(255,255,255,0.5);font-size:12px;margin-top:16px">Swipe anywhere to move your bird</p>
</div>
<div id="boost"><span style="font-size:26px">💨</span></div>
<div id="swipe-hint">👆 Swipe<br>to fly</div>
<script>
const CV=document.getElementById('c');
const ctx=CV.getContext('2d');
const COLS=12,ROWS=9;
let W,H,CELL,OX,OY;
let grid=[],player,enemies=[],running=false,raf;
let particles=[],floats=[],lastEn=0;
const BC={player:'rgba(50,205,50,0.35)',e0:'rgba(255,68,68,0.35)',e1:'rgba(68,136,255,0.35)',e2:'rgba(255,153,0,0.35)'};
const FC={player:'#7FFF7F',e0:'#FF8888',e1:'#88BBFF',e2:'#FFCC77',neutral:'#A8D5A2'};

function rs(){
  W=CV.width=window.innerWidth;
  H=CV.height=window.innerHeight;
  CELL=Math.min(Math.floor((W-10)/COLS),Math.floor((H-80)/ROWS));
  CELL=Math.max(CELL,32);
  OX=Math.floor((W-CELL*COLS)/2);
  OY=Math.floor((H-CELL*ROWS)/2)+16;
}
function cx(c){return OX+c*CELL+CELL/2}
function cy(r){return OY+r*CELL+CELL/2}
function gx(c){return OX+c*CELL}
function gy(r){return OY+r*CELL}

function ig(){
  grid=[];
  for(let r=0;r<ROWS;r++){
    grid[r]=[];
    for(let c=0;c<COLS;c++){
      grid[r][c]={owner:'neutral',nest:Math.random()<0.25,tree:Math.random()<0.1};
    }
  }
}

function mb(r,c,t,e){return{r,c,type:t,emoji:e,tr:[]};}

function cap(r,c,t){
  if(r<0||r>=ROWS||c<0||c>=COLS)return;
  grid[r][c].owner=t;
  if(grid[r][c].nest){
    spPt(cx(c),cy(r),t);
    addF('🏠',cx(c),cy(r));
    [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]].forEach(([dr,dc])=>{
      const nr=r+dr,nc=c+dc;
      if(nr>=0&&nr<ROWS&&nc>=0&&nc<COLS&&grid[nr][nc].owner!==t&&Math.random()<0.55)
        grid[nr][nc].owner=t;
    });
  }
}

function spPt(x,y,t){
  const col=FC[t]||'#fff';
  for(let i=0;i<7;i++){
    const a=Math.random()*Math.PI*2,s=2+Math.random()*5;
    particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-2,life:1,col,sz:3+Math.random()*5});
  }
}

function addF(t,x,y){floats.push({t,x,y:y-CELL*0.5,life:1,vy:-1.2});}

function mv(b,dr,dc){
  const nr=b.r+dr,nc=b.c+dc;
  if(nr<0||nr>=ROWS||nc<0||nc>=COLS)return false;
  b.r=nr;b.c=nc;
  b.tr.push({r:nr,c:nc});
  if(b.tr.length>5)b.tr.shift();
  cap(nr,nc,b.type);
  return true;
}

function gc(){
  let p=0,e=0,tot=ROWS*COLS;
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
    const o=grid[r][c].owner;
    if(o==='player')p++;else if(o!=='neutral')e++;
  }
  return{p,e,tot};
}

function uhud(){
  const{p,e,tot}=gc();
  const pct=Math.round(p/tot*100);
  document.getElementById('sn').textContent=p;
  document.getElementById('sp').textContent=pct+'%';
  document.getElementById('se').textContent=e;
  document.getElementById('pbf').style.width=pct+'%';
  if(pct>=65)eg(true);
  else if(e>=tot*0.72)eg(false);
}

function eg(win){
  running=false;cancelAnimationFrame(raf);
  const{p,tot}=gc();
  document.getElementById('screen').style.display='flex';
  document.getElementById('screen').innerHTML=
    '<h1>'+(win?'🏆 You Won!':'💔 Try Again!')+'</h1>'+
    '<p>'+(win?'Amazing! You ruled the sky!':'Rivals took over the aviary!')+
    '<br><b style="color:#FFE66D;font-size:20px">'+Math.round(p/tot*100)+'% territory</b></p>'+
    '<button class="btn" onclick="sg()">🔄 Play Again!</button>'+
    '<p style="color:rgba(255,255,255,0.5);font-size:11px;margin-top:14px">HannahBird.io · VNT World AI Division</p>';
}

// Touch/Swipe controls - no buttons, no keyboard
let tx=0,ty=0,ttime=0,moved=false;
document.addEventListener('touchstart',e=>{
  if(!running)return;
  tx=e.touches[0].clientX;ty=e.touches[0].clientY;
  ttime=Date.now();moved=false;
},{passive:true});

document.addEventListener('touchmove',e=>{
  if(!running||moved)return;
  const dx=e.touches[0].clientX-tx;
  const dy=e.touches[0].clientY-ty;
  const dist=Math.sqrt(dx*dx+dy*dy);
  if(dist<18)return;
  moved=true;
  if(Math.abs(dx)>Math.abs(dy))mv(player,0,dx>0?1:-1);
  else mv(player,dy>0?1:-1,0);
  uhud();
  // Reset for continuous swipe
  tx=e.touches[0].clientX;ty=e.touches[0].clientY;
  moved=false;
},{passive:true});

document.addEventListener('touchend',e=>{
  if(!running)return;
  if(!moved&&Date.now()-ttime<200){
    // Tap - move toward tap point
    const tapX=e.changedTouches[0].clientX;
    const tapY=e.changedTouches[0].clientY;
    const dx=tapX-cx(player.c);
    const dy=tapY-cy(player.r);
    if(Math.abs(dx)>Math.abs(dy))mv(player,0,dx>0?1:-1);
    else mv(player,dy>0?1:-1,0);
    uhud();
  }
},{passive:true});

document.getElementById('boost').addEventListener('touchstart',e=>{
  e.stopPropagation();
  if(!running)return;
  addF('💨 BOOST!',cx(player.c),cy(player.r));
  // Move in last direction 2 extra steps
  if(player.tr.length>=2){
    const last=player.tr[player.tr.length-1];
    const prev=player.tr[player.tr.length-2];
    const dr=last.r-prev.r,dc=last.c-prev.c;
    if(dr||dc){mv(player,dr,dc);uhud();setTimeout(()=>{mv(player,dr,dc);uhud();},100);}
  }
},{passive:true});

function tick(ts){
  if(!running)return;
  raf=requestAnimationFrame(tick);
  if(ts-lastEn>420){
    lastEn=ts;
    enemies.forEach(en=>{
      let bm=null,bs=-9;
      [[-1,0],[1,0],[0,-1],[0,1]].forEach(([dr,dc])=>{
        const nr=en.r+dr,nc=en.c+dc;
        if(nr<0||nr>=ROWS||nc<0||nc>=COLS)return;
        let sc=grid[nr][nc].owner==='player'?4:grid[nr][nc].owner==='neutral'?2:grid[nr][nc].owner===en.type?-1:1;
        if(grid[nr][nc].nest)sc+=3;sc+=Math.random()*2;
        if(sc>bs){bs=sc;bm=[dr,dc];}
      });
      if(bm)mv(en,bm[0],bm[1]);
    });
  }
  particles=particles.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=0.12;p.life-=0.05;return p.life>0;});
  floats=floats.filter(f=>{f.y+=f.vy;f.life-=0.022;return f.life>0;});
  draw();
}

function draw(){
  const sky=ctx.createLinearGradient(0,0,0,H);
  sky.addColorStop(0,'#87CEEB');sky.addColorStop(1,'#C8E6F5');
  ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);

  // Clouds
  ctx.fillStyle='rgba(255,255,255,0.55)';
  [[W*.15,40,60],[W*.55,25,75],[W*.82,35,50],[W*.38,55,40]].forEach(([x,y,s])=>{
    ctx.beginPath();ctx.arc(x,y,s/2,0,Math.PI*2);
    ctx.arc(x+s*.32,y-s*.18,s/3,0,Math.PI*2);
    ctx.arc(x-s*.28,y-s*.12,s/3,0,Math.PI*2);
    ctx.fill();
  });

  // Grid cells
  for(let r=0;r<ROWS;r++){
    for(let c=0;c<COLS;c++){
      const cell=grid[r][c],x=gx(c),y=gy(r);
      ctx.fillStyle=FC[cell.owner]||FC.neutral;
      ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,7);ctx.fill();
      ctx.strokeStyle='rgba(255,255,255,0.3)';ctx.lineWidth=1;
      ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,7);ctx.stroke();
      if(cell.tree&&cell.owner==='neutral'){
        ctx.font=Math.floor(CELL*.52)+'px serif';
        ctx.textAlign='center';ctx.textBaseline='middle';
        ctx.fillText('🌳',cx(c),cy(r));
      }
      if(cell.nest){
        ctx.font=Math.floor(CELL*.56)+'px serif';
        ctx.textAlign='center';ctx.textBaseline='middle';
        ctx.fillText('🪹',cx(c),cy(r));
      }
    }
  }

  // Trail
  player.tr.forEach((t,i)=>{
    ctx.fillStyle='rgba(50,205,50,'+(i/player.tr.length*.4)+')';
    ctx.beginPath();ctx.roundRect(gx(t.c)+5,gy(t.r)+5,CELL-10,CELL-10,4);ctx.fill();
  });

  // Birds
  [player,...enemies].forEach(b=>{
    const bx=cx(b.c),by=cy(b.r);
    // Shadow
    ctx.fillStyle='rgba(0,0,0,0.12)';
    ctx.beginPath();ctx.ellipse(bx,by+CELL*.36,CELL*.28,CELL*.09,0,0,Math.PI*2);ctx.fill();
    // Glow
    ctx.fillStyle=BC[b.type]||'rgba(255,255,255,0.3)';
    ctx.beginPath();ctx.arc(bx,by,CELL*.5,0,Math.PI*2);ctx.fill();
    // White circle
    ctx.fillStyle='rgba(255,255,255,0.92)';
    ctx.beginPath();ctx.arc(bx,by,CELL*.4,0,Math.PI*2);ctx.fill();
    // Bird
    ctx.font=Math.floor(CELL*.58)+'px serif';
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(b.emoji,bx,by+2);
    // YOU label
    if(b.type==='player'){
      ctx.fillStyle='rgba(0,0,0,0.7)';
      ctx.beginPath();ctx.roundRect(bx-22,by+CELL*.38,44,15,4);ctx.fill();
      ctx.fillStyle='#FFE66D';ctx.font='bold 9px sans-serif';
      ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText('YOU',bx,by+CELL*.46+7);
    }
  });

  // Particles
  particles.forEach(p=>{
    ctx.globalAlpha=p.life;ctx.fillStyle=p.col;
    ctx.beginPath();ctx.arc(p.x,p.y,p.sz*p.life,0,Math.PI*2);ctx.fill();
  });
  ctx.globalAlpha=1;

  // Float messages
  floats.forEach(f=>{
    ctx.globalAlpha=f.life;
    ctx.font='bold '+Math.floor(CELL*.35)+'px sans-serif';
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillStyle='rgba(0,0,0,0.6)';ctx.fillText(f.t,f.x+1,f.y+1);
    ctx.fillStyle='#FFE66D';ctx.fillText(f.t,f.x,f.y);
  });
  ctx.globalAlpha=1;
}

function sg(){
  document.getElementById('screen').style.display='none';
  document.getElementById('hud').style.display='block';
  document.getElementById('boost').style.display='flex';
  document.getElementById('swipe-hint').style.display='block';
  setTimeout(()=>document.getElementById('swipe-hint').style.display='none',3000);
  rs();ig();
  player=mb(Math.floor(ROWS/2),0,'player','🐦');
  enemies=[
    mb(Math.floor(ROWS/2),COLS-1,'e0','🦅'),
    mb(0,Math.floor(COLS/2),'e1','🦉'),
    mb(ROWS-1,Math.floor(COLS/2),'e2','🦚'),
  ];
  cap(player.r,player.c,'player');
  cap(enemies[0].r,enemies[0].c,'e0');
  cap(enemies[1].r,enemies[1].c,'e1');
  cap(enemies[2].r,enemies[2].c,'e2');
  particles=[];floats=[];
  addF('🐦 Go!',cx(player.c),cy(player.r));
  running=true;uhud();requestAnimationFrame(tick);
}

document.getElementById('sb').addEventListener('click',sg);
window.addEventListener('resize',rs);
rs();draw();
</script>
</body>
</html>"""

# Write mobile game
open("/home/k/vnt-web/hannahbird.html","w").write(mobile_html)
open("/home/k/vnt-web/generated/hannahbird.html","w").write(mobile_html)
os.makedirs(APP_DIR+"/www",exist_ok=True)
open(APP_DIR+"/www/index.html","w").write(mobile_html)
print("Mobile game HTML written (swipe only, no keyboard)")

# Sync capacitor
print("Syncing Capacitor...")
run("npx cap sync",cwd=APP_DIR,timeout=60)

# Build APK
print("Building APK...")
run("./gradlew assembleDebug --no-daemon 2>&1 | tail -30",cwd=APP_DIR+"/android",timeout=600)

apk_path=APP_DIR+"/android/app/build/outputs/apk/debug/app-debug.apk"
if os.path.exists(apk_path):
    shutil.copy(apk_path,"/home/k/vnt-web/generated/hannahbird.apk")
    size=os.path.getsize(apk_path)//1024
    print(f"APK built: {size}KB")

    # Deploy via WiFi ADB
    print("Connecting Redmi via WiFi...")
    r=subprocess.run(["adb","connect",REDMI_IP+":5555"],capture_output=True,text=True,timeout=10)
    print("WiFi ADB:",r.stdout.strip())
    time.sleep(3)

    devs=subprocess.run(["adb","devices"],capture_output=True,text=True).stdout
    print("Devices:",devs)

    installed=False
    for line in devs.split(chr(10))[1:]:
        if "device" in line and "List" not in line:
            dev=line.split()[0]
            print(f"Installing on {dev}...")
            ri=subprocess.run(["adb","-s",dev,"install","-r",apk_path],
                capture_output=True,text=True,timeout=90)
            out=ri.stdout.strip()+ri.stderr.strip()
            print("Install:",out[:150])
            if "Success" in out:
                installed=True
                print("INSTALLED SUCCESSFULLY on",dev)

    save("HannahBird APK deployed"+chr(10)+
        "Size: "+str(size)+"KB"+chr(10)+
        "WiFi install: "+str(installed)+chr(10)+
        "Download: http://192.168.10.96:3333/generated/hannahbird.apk"+chr(10)+
        "Web: http://192.168.10.96:8888/hannahbird.html")

    print("=== DONE ===")
    print("APK download: http://192.168.10.96:3333/generated/hannahbird.apk")
    print("Web play: http://192.168.10.96:8888/hannahbird.html")
else:
    print("Build failed - check Android SDK")
    run("find "+APP_DIR+" -name '*.apk' 2>/dev/null",timeout=10)
    save("HannahBird build failed - SDK issue")


import subprocess, os, shutil, time

GAME_DIR = "/home/k/vnt-web"
GAME_FILE = GAME_DIR + "/hannahbird.html"

game_html = open("/tmp/hannahbird.html").read() if False else """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>HannahBird.io</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{width:100%;height:100%;overflow:hidden;background:#87CEEB;touch-action:none}
canvas{display:block;position:fixed;top:0;left:0;width:100%;height:100%}
#hud{position:fixed;top:0;left:0;right:0;pointer-events:none;z-index:10}
#topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:rgba(0,0,0,0.4)}
#logo{font-size:22px;font-weight:900;color:#FFE66D;font-family:Comic Sans MS,cursive;text-shadow:2px 2px 0 #c0a800}
#logo em{color:#7FFF7F;font-style:normal}
.stat{text-align:center;background:rgba(255,255,255,0.15);border-radius:10px;padding:3px 12px;border:2px solid rgba(255,255,255,0.3)}
.sn{font-size:20px;font-weight:900;color:#FFE66D;font-family:Comic Sans MS,cursive}
.sl{font-size:9px;color:rgba(255,255,255,0.8);text-transform:uppercase;letter-spacing:1px}
#pb{height:10px;background:rgba(0,0,0,0.3);margin:3px 12px 0}
#pbf{height:100%;background:#32CD32;transition:width 0.4s;border-radius:5px}
#screen{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(0,0,0,0.6);z-index:20;font-family:Comic Sans MS,cursive}
#screen h1{font-size:min(52px,12vw);font-weight:900;color:#FFE66D;text-align:center;text-shadow:3px 3px 0 #c0a800;line-height:1.1}
#screen h1 em{color:#7FFF7F;font-style:normal}
#screen p{color:#fff;font-size:16px;margin:10px 0 22px;text-align:center;max-width:300px;line-height:1.5}
.btn{background:linear-gradient(135deg,#FFE66D,#FFA500);color:#1a0a00;border:none;padding:16px 40px;font-size:20px;font-weight:900;border-radius:50px;cursor:pointer;font-family:inherit;box-shadow:0 5px 0 #c06000;letter-spacing:0.5px}
.btn:active{transform:translateY(3px);box-shadow:0 2px 0 #c06000}
#dpad{position:fixed;bottom:16px;right:16px;width:140px;height:140px;z-index:10;pointer-events:all}
.dp{position:absolute;width:44px;height:44px;background:rgba(255,255,255,0.25);border:3px solid rgba(255,255,255,0.5);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;font-family:sans-serif}
.dp:active{background:rgba(255,255,255,0.5)}
#du{top:0;left:48px}#dd{bottom:0;left:48px}#dl{left:0;top:48px}#dr{right:0;top:48px}
#bb{position:fixed;bottom:16px;left:16px;width:64px;height:64px;background:linear-gradient(135deg,#FF6B6B,#FF3333);border:3px solid #fff;border-radius:50%;font-size:26px;cursor:pointer;pointer-events:all;z-index:10;display:flex;align-items:center;justify-content:center}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud" style="display:none">
  <div id="topbar">
    <div id="logo">Hannah<em>Bird</em>.io</div>
    <div class="stat"><div class="sn" id="sn">1</div><div class="sl">Nests</div></div>
    <div class="stat"><div class="sn" id="sp">0%</div><div class="sl">Territory</div></div>
    <div class="stat"><div class="sn" id="se">0</div><div class="sl">Rivals</div></div>
  </div>
  <div id="pb"><div id="pbf" style="width:2%;border-radius:5px"></div></div>
</div>
<div id="screen">
  <h1>Hannah<em>Bird</em>.io</h1>
  <p>Fly your bird<br>Capture nests<br>Rule the sky! 🌳</p>
  <button class="btn" id="sb">🐦 Play!</button>
</div>
<div id="dpad" style="display:none">
  <div class="dp" id="du">↑</div><div class="dp" id="dd">↓</div>
  <div class="dp" id="dl">←</div><div class="dp" id="dr">→</div>
</div>
<div id="bb" style="display:none">💨</div>
<script>
const CV=document.getElementById('c'),ctx=CV.getContext('2d');
const COLS=14,ROWS=10;
let W,H,CELL,OX,OY,grid=[],player,enemies=[],running=false,raf,keys={};
let particles=[],floats=[],lastKey=0,lastEn=0;
const BC={player:{g:'rgba(50,205,50,0.4)'},e0:{g:'rgba(255,68,68,0.4)'},e1:{g:'rgba(68,136,255,0.4)'},e2:{g:'rgba(255,153,0,0.4)'}};
function rs(){W=CV.width=window.innerWidth;H=CV.height=window.innerHeight;CELL=Math.min(Math.floor((W-20)/COLS),Math.floor((H-90)/ROWS));CELL=Math.max(CELL,30);OX=Math.floor((W-CELL*COLS)/2);OY=Math.floor((H-CELL*ROWS)/2)+20;}
function cx(c){return OX+c*CELL+CELL/2}function cy(r){return OY+r*CELL+CELL/2}function gx(c){return OX+c*CELL}function gy(r){return OY+r*CELL}
function ig(){grid=[];for(let r=0;r<ROWS;r++){grid[r]=[];for(let c=0;c<COLS;c++){grid[r][c]={owner:'neutral',nest:Math.random()<0.28,tree:Math.random()<0.12};}}}
function mb(r,c,t,e){return{r,c,type:t,emoji:e,tr:[]};}
function cap(r,c,t,sp=1){if(r<0||r>=ROWS||c<0||c>=COLS)return;const prev=grid[r][c].owner;grid[r][c].owner=t;if(sp&&grid[r][c].nest){spParts(cx(c),cy(r),t);addF('🏠+',cx(c),cy(r));const ds=[[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]];ds.forEach(([dr,dc])=>{const nr=r+dr,nc=c+dc;if(nr>=0&&nr<ROWS&&nc>=0&&nc<COLS&&grid[nr][nc].owner!==t&&Math.random()<0.5)grid[nr][nc].owner=t;});}}
function spParts(x,y,t){const c=t==='player'?'#7FFF7F':t==='e0'?'#FF8888':t==='e1'?'#88BBFF':'#FFCC77';for(let i=0;i<6;i++){const a=Math.random()*Math.PI*2,s=2+Math.random()*4;particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-2,life:1,c,sz:3+Math.random()*5});}}
function addF(t,x,y){floats.push({t,x,y:y-20,life:1,vy:-1.5});}
function mv(b,dr,dc){const nr=b.r+dr,nc=b.c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)return;b.r=nr;b.c=nc;b.tr.push({r:nr,c:nc});if(b.tr.length>5)b.tr.shift();cap(nr,nc,b.type,1);}
function gc2(){let p=0,e=0,n=0,tot=ROWS*COLS;for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){const o=grid[r][c].owner;if(o==='player')p++;else if(o!=='neutral')e++;else n++;}return{p,e,n,tot};}
function uhud(){const{p,e,tot}=gc2();const pct=Math.round(p/tot*100);document.getElementById('sn').textContent=p;document.getElementById('sp').textContent=pct+'%';document.getElementById('se').textContent=e;document.getElementById('pbf').style.width=pct+'%';if(pct>=65)eg(true);else if(e>=tot*0.72)eg(false);}
document.addEventListener('keydown',e=>{keys[e.key]=true;});
document.addEventListener('keyup',e=>{keys[e.key]=false;});
function sdp(){
  document.getElementById('dpad').style.display='block';document.getElementById('bb').style.display='flex';
  const mp={du:[-1,0],dd:[1,0],dl:[0,-1],dr:[0,1]};
  Object.entries(mp).forEach(([id,d])=>{const b=document.getElementById(id);let iv=null;const go=()=>{mv(player,d[0],d[1]);uhud();};b.addEventListener('pointerdown',e=>{e.preventDefault();go();iv=setInterval(go,160);});b.addEventListener('pointerup',()=>clearInterval(iv));b.addEventListener('pointerleave',()=>clearInterval(iv));});
  document.getElementById('bb').addEventListener('pointerdown',e=>{e.preventDefault();addF('💨 Boost!',cx(player.c),cy(player.r));for(let i=0;i<2;i++)setTimeout(()=>mv(player,0,0),i*60);});
  let tx=0,ty=0;
  CV.addEventListener('touchstart',e=>{tx=e.touches[0].clientX;ty=e.touches[0].clientY;},{passive:true});
  CV.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-tx,dy=e.changedTouches[0].clientY-ty;if(Math.abs(dx)+Math.abs(dy)<15)return;if(Math.abs(dx)>Math.abs(dy))mv(player,0,dx>0?1:-1);else mv(player,dy>0?1:-1,0);uhud();},{passive:true});
}
function eg(win){running=false;cancelAnimationFrame(raf);const{p,tot}=gc2();document.getElementById('screen').style.display='flex';document.getElementById('screen').innerHTML=`<h1>${win?'🏆 Won!':'💔 Retry!'}</h1><p>${win?'You captured the sky!':'Rivals took over!'}<br><strong style="color:#FFE66D">${Math.round(p/tot*100)}%</strong> territory</p><button class="btn" onclick="sg()">🔄 Play Again</button>`;}
function sg(){document.getElementById('screen').style.display='none';document.getElementById('hud').style.display='block';document.getElementById('dpad').style.display='block';document.getElementById('bb').style.display='flex';rs();ig();player=mb(4,1,'player','🐦');enemies=[mb(4,COLS-2,'e0','🦅'),mb(1,Math.floor(COLS/2),'e1','🦉'),mb(ROWS-2,Math.floor(COLS/2),'e2','🦚')];cap(4,1,'player',0);cap(4,COLS-2,'e0',0);cap(1,Math.floor(COLS/2),'e1',0);cap(ROWS-2,Math.floor(COLS/2),'e2',0);particles=[];floats=[];addF('🐦 Go!',cx(1),cy(4));running=true;uhud();requestAnimationFrame(tick);}
function tick(ts){if(!running)return;raf=requestAnimationFrame(tick);if(ts-lastKey>120){if(keys['ArrowUp']||keys['w']){mv(player,-1,0);lastKey=ts;}else if(keys['ArrowDown']||keys['s']){mv(player,1,0);lastKey=ts;}else if(keys['ArrowLeft']||keys['a']){mv(player,0,-1);lastKey=ts;}else if(keys['ArrowRight']||keys['d']){mv(player,0,1);lastKey=ts;}if(lastKey===ts)uhud();}
if(ts-lastEn>450){lastEn=ts;enemies.forEach(en=>{const ms=[[-1,0],[1,0],[0,-1],[0,1]];let bm=null,bs=-9;ms.forEach(([dr,dc])=>{const nr=en.r+dr,nc=en.c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)return;let sc=grid[nr][nc].owner==='player'?4:grid[nr][nc].owner==='neutral'?2:grid[nr][nc].owner===en.type?-1:1;if(grid[nr][nc].nest)sc+=3;sc+=Math.random()*1.5;if(sc>bs){bs=sc;bm=[dr,dc];}});if(bm)mv(en,bm[0],bm[1]);});}
particles=particles.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=0.12;p.life-=0.05;return p.life>0;});floats=floats.filter(f=>{f.y+=f.vy;f.life-=0.025;return f.life>0;});draw();}
function draw(){const sky=ctx.createLinearGradient(0,0,0,H);sky.addColorStop(0,'#87CEEB');sky.addColorStop(1,'#E0F7FA');ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);
ctx.fillStyle='rgba(255,255,255,0.5)';[[W*0.2,35,55],[W*0.6,22,70],[W*0.85,38,45]].forEach(([x,y,s])=>{ctx.beginPath();ctx.arc(x,y,s/2,0,Math.PI*2);ctx.arc(x+s*.3,y-s*.15,s/3,0,Math.PI*2);ctx.arc(x-s*.3,y-s*.1,s/3,0,Math.PI*2);ctx.fill();});
for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){const cell=grid[r][c],x=gx(c),y=gy(r);const fc=cell.owner==='player'?'#7FFF7F':cell.owner==='e0'?'#FF8888':cell.owner==='e1'?'#88BBFF':cell.owner==='e2'?'#FFCC77':'#A8D5A2';ctx.fillStyle=fc;ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,6);ctx.fill();ctx.strokeStyle='rgba(255,255,255,0.35)';ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,6);ctx.stroke();if(cell.tree&&cell.owner==='neutral'){ctx.font=`${CELL*.5}px serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('🌳',cx(c),cy(r));}if(cell.nest){ctx.font=`${CELL*.55}px serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('🪹',cx(c),cy(r));}}
player.tr.forEach((t,i)=>{ctx.fillStyle=`rgba(50,205,50,${(i/player.tr.length)*0.45})`;ctx.beginPath();ctx.roundRect(gx(t.c)+4,gy(t.r)+4,CELL-8,CELL-8,4);ctx.fill();});
[player,...enemies].forEach(b=>{const bx=cx(b.c),by=cy(b.r),bc=BC[b.type];ctx.fillStyle='rgba(0,0,0,0.15)';ctx.beginPath();ctx.ellipse(bx,by+CELL*.35,CELL*.28,CELL*.1,0,0,Math.PI*2);ctx.fill();ctx.fillStyle=bc.g;ctx.beginPath();ctx.arc(bx,by,CELL*.5,0,Math.PI*2);ctx.fill();ctx.fillStyle='rgba(255,255,255,0.9)';ctx.beginPath();ctx.arc(bx,by,CELL*.4,0,Math.PI*2);ctx.fill();ctx.font=`${Math.floor(CELL*.56)}px serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(b.emoji,bx,by+2);if(b.type==='player'){ctx.fillStyle='rgba(0,0,0,0.65)';ctx.beginPath();ctx.roundRect(bx-20,by+CELL*.38,40,15,4);ctx.fill();ctx.fillStyle='#FFE66D';ctx.font='bold 9px sans-serif';ctx.fillText('YOU',bx,by+CELL*.46+7);}});
particles.forEach(p=>{ctx.globalAlpha=p.life;ctx.fillStyle=p.c;ctx.beginPath();ctx.arc(p.x,p.y,p.sz*p.life,0,Math.PI*2);ctx.fill();});ctx.globalAlpha=1;
floats.forEach(f=>{ctx.globalAlpha=f.life;ctx.font='bold 15px Comic Sans MS,cursive';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#000';ctx.fillText(f.t,f.x+1,f.y+1);ctx.fillStyle='#FFE66D';ctx.fillText(f.t,f.x,f.y);});ctx.globalAlpha=1;}
document.getElementById('sb').addEventListener('click',()=>{sdp();sg();});
window.addEventListener('resize',rs);rs();draw();
</script>
</body>
</html>"""

open(GAME_FILE,"w").write(game_html)
print("Game deployed:", GAME_FILE)

# Copy to generated for easy access
import shutil
shutil.copy(GAME_FILE, "/home/k/vnt-web/generated/hannahbird.html")
print("Also at: /home/k/vnt-web/generated/hannahbird.html")

# Save to MemPalace
import datetime
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md","a").write(
    chr(10)+"### HannahBird.io Game Deployed ["+ts+"]"+chr(10)+
    "Web: http://192.168.10.96:8888/hannahbird.html"+chr(10)+
    "Mirror: http://192.168.10.96:3333/generated/hannahbird.html"+chr(10)+
    "Features: Touch+swipe, D-pad, boost, particles, nests, AI enemies"+chr(10)
)

print("=========================")
print("GAME LIVE:")
print("http://192.168.10.96:8888/hannahbird.html")
print("=========================")
print("For APK: Use Capacitor to wrap this HTML into Android APK")
print("Run: npm install -g @capacitor/cli && npx cap init")

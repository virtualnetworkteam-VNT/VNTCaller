
import subprocess, os, shutil, datetime

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
WEB = "/home/k/vnt-web"
APP_WWW = "/home/k/hannahbird-app/www"
GAME_PATH = "/tmp/hannahbird_new.html"
JAVA = "JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64"

os.makedirs(APP_WWW, exist_ok=True)

# Download game from github raw or write directly
# Write game line by line to avoid escape issues
lines = [
'<!DOCTYPE html>',
'<html lang="en">',
'<head>',
'<meta charset="utf-8">',
'<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">',
'<meta name="mobile-web-app-capable" content="yes">',
'<meta name="apple-mobile-web-app-capable" content="yes">',
'<title>HannahBird.io</title>',
'<style>',
'*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}',
'html,body{width:100%;height:100%;overflow:hidden;touch-action:none;background:#87CEEB;font-family:sans-serif}',
'canvas{position:fixed;top:0;left:0;width:100vw;height:100vh;display:block}',
'#hud{position:fixed;top:0;left:0;right:0;z-index:10;pointer-events:none}',
'#top{display:flex;justify-content:space-between;align-items:center;padding:max(env(safe-area-inset-top,6px),6px) 10px 6px;background:rgba(0,0,0,0.5)}',
'#logo{font-size:clamp(16px,4.5vw,22px);font-weight:900;color:#FFE66D}',
'#logo b{color:#90EE90}',
'.hs{background:rgba(255,255,255,0.12);border-radius:8px;padding:2px clamp(6px,2.5vw,12px);text-align:center;border:1.5px solid rgba(255,255,255,0.25);min-width:clamp(44px,12vw,60px)}',
'.sn{font-size:clamp(15px,4.5vw,20px);font-weight:900;color:#FFE66D}',
'.sl{font-size:clamp(8px,2vw,10px);color:rgba(255,255,255,0.65);text-transform:uppercase}',
'#pb{height:clamp(5px,1.5vw,8px);background:rgba(0,0,0,0.3)}',
'#pbf{height:100%;background:linear-gradient(90deg,#7FFF7F,#32CD32);transition:width .4s}',
'#ov{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(5,10,20,0.92);z-index:30;padding:16px;overflow-y:auto}',
'#ov h1{font-size:clamp(28px,8vw,44px);font-weight:900;color:#FFE66D;text-shadow:3px 3px 0 #8B6914;text-align:center;line-height:1.1;margin-bottom:4px}',
'#ov h1 b{color:#90EE90}',
'.sub{color:#bbb;font-size:clamp(12px,3.5vw,15px);text-align:center;margin:0 0 10px;line-height:1.5}',
'.row{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin:3px 0}',
'.p{background:rgba(255,255,255,0.07);border:1.5px solid rgba(255,255,255,0.18);border-radius:18px;padding:clamp(5px,1.5vw,8px) clamp(10px,3vw,14px);cursor:pointer;font-size:clamp(12px,3.2vw,14px);color:#ccc;white-space:nowrap}',
'.p.on,.p:active{background:rgba(255,220,0,0.18);border-color:#FFE66D;color:#FFE66D;font-weight:700}',
'.lbl{font-size:clamp(9px,2.2vw,11px);color:#666;display:block;margin:6px 0 2px;text-align:center;text-transform:uppercase;letter-spacing:.5px}',
'input[type=text]{background:rgba(255,255,255,0.08);border:1.5px solid rgba(255,255,255,0.2);border-radius:8px;color:#fff;padding:7px 10px;font-size:clamp(13px,3.5vw,15px);text-align:center;width:clamp(140px,40vw,180px);outline:none}',
'input[type=text]:focus{border-color:#FFE66D}',
'.gbtn{background:linear-gradient(135deg,#FFE66D,#FFA500);color:#1a0a00;border:none;padding:clamp(10px,3vw,14px) clamp(22px,6vw,32px);font-size:clamp(15px,4.5vw,19px);font-weight:900;border-radius:50px;cursor:pointer;box-shadow:0 5px 0 #8B6914;margin:4px}',
'.gbtn:active{transform:translateY(3px);box-shadow:0 2px 0 #8B6914}',
'.gbtn2{background:rgba(255,255,255,0.08);color:#888;border:1.5px solid rgba(255,255,255,0.15);border-radius:50px;padding:clamp(8px,2.5vw,11px) clamp(16px,5vw,22px);font-size:clamp(12px,3.5vw,14px);font-weight:700;margin:4px}',
'#bst{position:fixed;bottom:max(env(safe-area-inset-bottom,14px),14px);left:14px;width:clamp(56px,15vw,68px);height:clamp(56px,15vw,68px);background:rgba(255,100,50,.88);border:3px solid #fff;border-radius:50%;font-size:clamp(22px,7vw,28px);cursor:pointer;z-index:10;display:none;align-items:center;justify-content:center;flex-direction:column}',
'#bst span{font-size:clamp(7px,2vw,9px);color:#fff;font-weight:700}',
'#qbtn{position:fixed;bottom:max(env(safe-area-inset-bottom,14px),14px);right:14px;background:rgba(200,40,40,.85);border:1.5px solid rgba(255,255,255,.35);border-radius:8px;color:#fff;padding:9px 14px;font-size:clamp(11px,3vw,13px);font-weight:700;cursor:pointer;z-index:10;display:none}',
'#lbadge{position:fixed;top:max(env(safe-area-inset-top,46px),46px);right:10px;background:rgba(0,0,0,.6);border-radius:7px;padding:3px 9px;font-size:clamp(10px,2.5vw,12px);font-weight:700;color:#FFE66D;z-index:10;display:none;border:1.5px solid rgba(255,220,0,.35)}',
'#pwt{position:fixed;top:max(env(safe-area-inset-top,46px),46px);left:10px;background:rgba(0,0,0,.6);border-radius:7px;padding:3px 9px;font-size:clamp(10px,2.5vw,12px);font-weight:700;color:#FFE66D;z-index:10;display:none}',
'#micon{position:fixed;top:max(env(safe-area-inset-top,46px),46px);right:10px;width:clamp(28px,8vw,36px);height:clamp(28px,8vw,36px);background:rgba(0,0,0,.55);border-radius:50%;display:none;align-items:center;justify-content:center;font-size:clamp(14px,4vw,18px);cursor:pointer;z-index:11;border:1.5px solid rgba(255,255,255,.3)}',
'</style>',
'</head>',
'<body>',
'<canvas id="c"></canvas>',
'<div id="hud" style="display:none">',
'  <div id="top">',
'    <div id="logo">Hannah<b>Bird</b>.io</div>',
'    <div class="hs"><div class="sn" id="sn">0</div><div class="sl">Nests</div></div>',
'    <div class="hs"><div class="sn" id="sp">0%</div><div class="sl">Area</div></div>',
'    <div class="hs"><div class="sn" id="sc">0</div><div class="sl">Score</div></div>',
'    <div class="hs"><div class="sn" id="se">0</div><div class="sl">Rivals</div></div>',
'  </div>',
'  <div id="pb"><div id="pbf" style="width:2%"></div></div>',
'</div>',
'<div id="lbadge"></div><div id="pwt"></div>',
'<div id="micon">&#128266;</div>',
'<div id="bst" style="display:none"><span style="font-size:clamp(20px,6vw,26px)">&#128168;</span><span>BOOST</span></div>',
'<div id="qbtn" style="display:none">&#10005; Quit</div>',
'<div id="ov">',
'  <h1>Hannah<b>Bird</b>.io</h1>',
'  <p class="sub">Capture nests &#183; Grow your flock &#183; Rule the sky!</p>',
'  <div id="olc">',
'    <div style="display:flex;gap:14px;flex-wrap:wrap;justify-content:center">',
'      <div><span class="lbl">Your bird</span>',
'        <div class="row" id="bp">',
'          <div class="p on" data-v="&#x1F426;">&#x1F426; Sparrow</div>',
'          <div class="p" data-v="&#x1F54A;&#xFE0F;">&#x1F54A;&#xFE0F; Pigeon</div>',
'          <div class="p" data-v="&#x1F99C;">&#x1F99C; Parrot</div>',
'          <div class="p" data-v="&#x1F985;">&#x1F985; Eagle</div>',
'          <div class="p" data-v="&#x1F99A;">&#x1F99A; Peacock</div>',
'          <div class="p" data-v="&#x1F989;">&#x1F989; Owl</div>',
'          <div class="p" data-v="&#x1F427;">&#x1F427; Penguin</div>',
'        </div>',
'      </div>',
'      <div><span class="lbl">Name your bird</span>',
'        <input type="text" id="bname" value="Hannah" maxlength="12">',
'      </div>',
'    </div>',
'    <div style="display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin-top:6px">',
'      <div><span class="lbl">Color</span>',
'        <div class="row" id="cp">',
'          <div class="p on" data-v="default">Default</div>',
'          <div class="p" data-v="#7FFF7F">Green</div>',
'          <div class="p" data-v="#87CEFA">Blue</div>',
'          <div class="p" data-v="#FFB347">Orange</div>',
'          <div class="p" data-v="#FF69B4">Pink</div>',
'          <div class="p" data-v="#FFD700">Gold</div>',
'          <div class="p" data-v="#CC88FF">Purple</div>',
'        </div>',
'      </div>',
'      <div><span class="lbl">Difficulty</span>',
'        <div class="row" id="dp">',
'          <div class="p on" data-v="easy">&#x1F423; Easy</div>',
'          <div class="p" data-v="medium">&#x1F414; Medium</div>',
'          <div class="p" data-v="hard">&#x1F981; Hard</div>',
'          <div class="p" data-v="speed">&#x26A1; Speed</div>',
'        </div>',
'      </div>',
'    </div>',
'    <div style="display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin-top:6px">',
'      <div><span class="lbl">Sky theme</span>',
'        <div class="row" id="tp">',
'          <div class="p on" data-v="auto">&#x1F305; Auto</div>',
'          <div class="p" data-v="day">&#x2600;&#xFE0F; Day</div>',
'          <div class="p" data-v="evening">&#x1F307; Evening</div>',
'          <div class="p" data-v="night">&#x1F319; Night</div>',
'        </div>',
'      </div>',
'      <div><span class="lbl">Music</span>',
'        <div class="row" id="mp">',
'          <div class="p on" data-v="on">&#x1F3B5; On</div>',
'          <div class="p" data-v="off">&#x1F507; Off</div>',
'        </div>',
'      </div>',
'    </div>',
'    <div class="row" style="margin-top:14px">',
'      <button class="gbtn" id="startbtn">&#x1F426; Start Playing!</button>',
'      <div class="gbtn2">&#x1F310; Multiplayer<br><span style="font-size:10px;opacity:.6">Coming Soon</span></div>',
'    </div>',
'    <div style="color:#444;font-size:10px;text-align:center;margin-top:8px">Unlimited Levels &#183; VNT World AI Division</div>',
'  </div>',
'</div>',
'<script>',
'const CV=document.getElementById("c"),ctx=CV.getContext("2d");',
'let W,H,COLS,ROWS=9,CELL,OX,OY;',
'let grid=[],player,enemies=[],running=false,raf;',
'let pts=[],fts=[];',
'let score=0,level=1,lvlScore=0,combo=0;',
'let pBird="\u{1F426}",pName="Hannah",pColor="default",diff="easy",tod="auto",musicOn=true;',
'let pwA={speed:0,fire:0,area:0,super:0},lastEn=0,lastKey=0,lastSuper=0;',
'let tx0=0,ty0=0,tmoved=false,AC=null,musicPlaying=false;',
'function rs(){W=CV.width=window.innerWidth;H=CV.height=window.innerHeight;const m=Math.min(W,H);COLS=W>H?Math.min(14,Math.max(10,Math.floor(W/(m/10)))):Math.min(10,Math.max(8,Math.floor(W/(m/9))));CELL=Math.min(Math.floor((W-6)/COLS),Math.floor((H-70)/ROWS));CELL=Math.max(CELL,Math.floor(m/11));OX=Math.floor((W-CELL*COLS)/2);OY=Math.floor((H-CELL*ROWS)/2)+8;}',
'function cx(c){return OX+c*CELL+CELL/2}function cy(r){return OY+r*CELL+CELL/2}',
'function gx(c){return OX+c*CELL}function gy(r){return OY+r*CELL}',
'function sel(gid,el,fn){document.querySelectorAll("#"+gid+" .p").forEach(e=>e.classList.remove("on"));el.classList.add("on");fn(el.dataset.v);}',
'document.querySelectorAll("#bp .p").forEach(e=>e.onclick=()=>sel("bp",e,v=>pBird=v));',
'document.querySelectorAll("#cp .p").forEach(e=>e.onclick=()=>sel("cp",e,v=>pColor=v));',
'document.querySelectorAll("#dp .p").forEach(e=>e.onclick=()=>sel("dp",e,v=>diff=v));',
'document.querySelectorAll("#tp .p").forEach(e=>e.onclick=()=>sel("tp",e,v=>tod=v));',
'document.querySelectorAll("#mp .p").forEach(e=>e.onclick=()=>{sel("mp",e,v=>musicOn=v==="on");if(!musicOn)stopMusic();else if(running)startMusic();});',
'function getC(){return pColor==="default"?"#7FFF7F":pColor;}',
'function getAC(){if(!AC)try{AC=new(window.AudioContext||window.webkitAudioContext)();}catch(e){}return AC;}',
'function playFX(t){if(!musicOn)return;const ac=getAC();if(!ac)return;const s={nest:[660,880,.18,.18],win:[523,1046,.28,.5],lose:[440,220,.22,.4],speed:[880,1200,.18,.15],fire:[300,150,.18,.2],area:[550,750,.22,.2],super:[440,880,.28,.4],start:[523,659,.18,.3],lvl:[660,1320,.28,.5]};const[f1,f2,vol,dur]=s[t]||[440,440,.13,.2];const o=ac.createOscillator(),g=ac.createGain();o.frequency.setValueAtTime(f1,ac.currentTime);o.frequency.exponentialRampToValueAtTime(f2,ac.currentTime+dur);g.gain.setValueAtTime(vol,ac.currentTime);g.gain.exponentialRampToValueAtTime(.001,ac.currentTime+dur);o.connect(g);g.connect(ac.destination);o.start();o.stop(ac.currentTime+dur+.05);}',
'function startMusic(){if(!musicOn||musicPlaying)return;const ac=getAC();if(!ac)return;musicPlaying=true;const mg=ac.createGain();mg.gain.value=.14;mg.connect(ac.destination);const ns=[261.63,293.66,329.63,392,440,523.25,587.33,659.25,783.99,880];const ml=[0,2,4,7,9,12,9,7,4,2,0,4,7,9,12,9,2,4,7,4,0,4,9,7,0,2,4,7,4,2,0,4].map(i=>ns[i%ns.length]);const beat=60/155;let t=ac.currentTime+.1;function loop(){ml.forEach((f,i)=>{const o=ac.createOscillator(),g=ac.createGain();o.type="square";o.frequency.value=f;g.gain.setValueAtTime(0,t+i*beat*.5);g.gain.linearRampToValueAtTime(.32,t+i*beat*.5+.02);g.gain.exponentialRampToValueAtTime(.001,t+i*beat*.5+beat*.42);o.connect(g);g.connect(mg);o.start(t+i*beat*.5);o.stop(t+i*beat*.5+beat*.5);});[65.41,73.42,82.41,87.31,65.41,82.41,87.31,73.42].forEach((f,i)=>{const o=ac.createOscillator(),g=ac.createGain();o.type="sawtooth";o.frequency.value=f;g.gain.setValueAtTime(0,t+i*beat*2);g.gain.linearRampToValueAtTime(.18,t+i*beat*2+.05);g.gain.exponentialRampToValueAtTime(.001,t+i*beat*2+beat*1.8);o.connect(g);g.connect(mg);o.start(t+i*beat*2);o.stop(t+i*beat*2+beat*2);});const ll=ml.length*beat*.5;t+=ll;if(musicPlaying)setTimeout(loop,(ll-.4)*1000);}loop();}',
'function stopMusic(){musicPlaying=false;}',
'document.getElementById("micon").onclick=()=>{musicOn=!musicOn;document.getElementById("micon").textContent=musicOn?"&#128266;":"&#128263;";if(!musicOn)stopMusic();else startMusic();};',
'function ig(){grid=[];for(let r=0;r<ROWS;r++){grid[r]=[];for(let c=0;c<COLS;c++){const rnd=Math.random();grid[r][c]={owner:"neutral",nest:rnd<.2,tree:rnd>=.2&&rnd<.3,pw:rnd>=.3&&rnd<.38?["speed","fire","area","super"][Math.floor(Math.random()*4)]:null};}}}',
'function mb(r,c,t,e){return{r,c,type:t,emoji:e,tr:[],frozen:0};}',
'function getFC(t){return t==="player"?getC():t==="e0"?"#FF8888":t==="e1"?"#88BBFF":"#FFCC77";}',
'function cap(r,c,t,sp=true){if(r<0||r>=ROWS||c<0||c>=COLS)return;grid[r][c].owner=t;if(grid[r][c].pw&&t==="player"){apw(grid[r][c].pw,r,c);grid[r][c].pw=null;}if(t==="player"){score+=combo>3?2:1;lvlScore++;combo++;}if(sp&&grid[r][c].nest){spPts(cx(c),cy(r),getFC(t));addF(t==="player"?"Home"+(combo>3?"+2":"+1"):"Home",cx(c),cy(r));if(t==="player"&&musicOn)playFX("nest");const sr=t==="player"?(pwA.area>Date.now()?3:2):1,bn=diff==="easy"?.2:0;for(let dr=-sr;dr<=sr;dr++)for(let dc=-sr;dc<=sr;dc++){if(Math.abs(dr)+Math.abs(dc)<=sr){const nr=r+dr,nc=c+dc;if(nr>=0&&nr<ROWS&&nc>=0&&nc<COLS&&grid[nr][nc].owner!==t&&Math.random()<(t==="player"?.64+bn:.44)){grid[nr][nc].owner=t;if(t==="player"){score++;lvlScore++;}}}}}}',
'function apw(type,r,c){pwA[type]=Date.now()+(type==="super"?12000:5000);const m={speed:"Wind Speed!",fire:"Fire Power!",area:"Area Blast!",super:"Supercharge!"};addF(m[type],cx(c),cy(r));spPts(cx(c),cy(r),"#FFD700");if(musicOn)playFX(type);}',
'function spPts(x,y,col){for(let i=0;i<8;i++){const a=Math.random()*Math.PI*2,s=3+Math.random()*5;pts.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-2,life:1,col,sz:4+Math.random()*6});}}',
'function addF(t,x,y){fts.push({t,x,y:y-CELL*.6,life:1,vy:-1.5});}',
'function mv(b,dr,dc){if(b.frozen>Date.now())return false;const nr=b.r+dr,nc=b.c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)return false;b.r=nr;b.c=nc;b.tr.push({r:nr,c:nc});if(b.tr.length>6)b.tr.shift();if(b.type==="player"&&pwA.fire>Date.now()){[[-1,0],[1,0],[0,-1],[0,1]].forEach(([fr,fc])=>{const er=nr+fr,ec=nc+fc;if(er>=0&&er<ROWS&&ec>=0&&ec<COLS){const tgt=enemies.find(e=>e.r===er&&e.c===ec);if(tgt){tgt.frozen=Date.now()+2500;addF("FIRE!",cx(ec),cy(er));}}});}cap(nr,nc,b.type,true);return true;}',
'function gc(){let p=0,e=0,tot=ROWS*COLS;for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){const o=grid[r][c].owner;if(o==="player")p++;else if(o!=="neutral")e++;}return{p,e,tot};}',
'function uhud(){const{p,e,tot}=gc();const pct=Math.round(p/tot*100);document.getElementById("sn").textContent=p;document.getElementById("sp").textContent=pct+"%";document.getElementById("sc").textContent=score;document.getElementById("se").textContent=e;document.getElementById("pbf").style.width=pct+"%";if(pct>=(65+(diff==="easy"?10:0)))nextLevel();else if(e>=tot*(diff==="easy"?.8:.68))endGame(false);}',
'function ecnt(){return level<5?1:level<10?2:3;}',
'function nextLevel(){level++;lvlScore=0;combo=0;running=false;cancelAnimationFrame(raf);stopMusic();if(musicOn)playFX("lvl");showMsg("Level "+(level-1)+" Complete!","Score: "+score+" - "+pName+" is amazing!","Level "+level+"!",continueGame,false);}',
'function endGame(win){running=false;cancelAnimationFrame(raf);stopMusic();const{p,tot}=gc();if(musicOn)playFX(win?"win":"lose");showMsg(win?pName+" Won!":"So close!","Level "+level+" Score: "+score+" - "+Math.round(p/tot*100)+"% territory",win?"Play Again":"Try Again",()=>{level=1;score=0;go();},true);}',
'function showMsg(title,sub,btn,cb,home=false){const ov=document.getElementById("ov"),olc=document.getElementById("olc");ov.style.display="flex";document.getElementById("hud").style.display="none";["bst","qbtn","lbadge","pwt","micon"].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display="none";});olc.innerHTML="<div style=\'text-align:center;padding:10px\'><div style=\'color:#FFE66D;font-size:clamp(20px,6vw,26px);font-weight:900;margin-bottom:6px\'>"+title+"</div><div style=\'color:#aaa;font-size:clamp(12px,3.5vw,15px);margin-bottom:18px\'>"+sub+"</div><div style=\'display:flex;gap:10px;justify-content:center;flex-wrap:wrap\'><button class=\'gbtn\' onclick=\'("+cb.toString()+")()\'> "+btn+"</button>"+(home?"<button class=\'gbtn2\' onclick=\'location.reload()\' style=\'cursor:pointer;opacity:1;color:#ccc\'>Menu</button>":"")+"</div><div style=\'color:#444;font-size:10px;margin-top:10px\'>Unlimited Levels - VNT World AI Division</div></div>";}',
'function continueGame(){document.getElementById("ov").style.display="none";document.getElementById("hud").style.display="block";["bst","micon"].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display="flex";});document.getElementById("qbtn").style.display="block";document.getElementById("lbadge").style.display="block";document.getElementById("lbadge").textContent="Lv "+level;document.getElementById("micon").textContent=musicOn?"&#128266;":"&#128263;";rs();ig();lvlScore=0;combo=0;const ec=ecnt(),pos=[[Math.floor(ROWS/2),0],[Math.floor(ROWS/2),COLS-1],[0,Math.floor(COLS/2)],[ROWS-1,Math.floor(COLS/2)]];player=mb(pos[0][0],pos[0][1],"player",pBird);enemies=[];const ee=["Eagle","Owl","Bird"];for(let i=0;i<ec;i++)enemies.push(mb(pos[i+1][0],pos[i+1][1],"e"+i,["&#x1F985;","&#x1F989;","&#x1F99A;"][i]));cap(player.r,player.c,"player",false);enemies.forEach((e,i)=>cap(e.r,e.c,"e"+i,false));pts=[];fts=[];pwA={speed:0,fire:0,area:0,super:0};lastSuper=Date.now();addF("Go "+pName+"!",cx(player.c),cy(player.r));running=true;uhud();requestAnimationFrame(tick);if(musicOn){getAC()?.resume?.();startMusic();}}',
'function go(){pName=document.getElementById("bname")?.value||pName;continueGame();if(musicOn)playFX("start");}',
'document.getElementById("startbtn").onclick=go;',
'document.getElementById("bst").addEventListener("click",e=>{e.stopPropagation();if(!running)return;if(player.tr.length>=2){const l=player.tr[player.tr.length-1],p2=player.tr[player.tr.length-2];const dr=l.r-p2.r,dc=l.c-p2.c;if(dr||dc){mv(player,dr,dc);mv(player,dr,dc);combo++;uhud();}}});',
'document.getElementById("qbtn").onclick=()=>endGame(false);',
'let keys={};document.addEventListener("keydown",e=>{keys[e.key]=true;});document.addEventListener("keyup",e=>{keys[e.key]=false;});',
'document.addEventListener("touchstart",e=>{if(!running)return;tx0=e.touches[0].clientX;ty0=e.touches[0].clientY;tmoved=false;},{passive:true});',
'document.addEventListener("touchmove",e=>{if(!running||tmoved)return;const dx=e.touches[0].clientX-tx0,dy=e.touches[0].clientY-ty0;if(Math.sqrt(dx*dx+dy*dy)<CELL*.28)return;tmoved=true;const sp=pwA.speed>Date.now()?2:1;if(Math.abs(dx)>Math.abs(dy)){for(let i=0;i<sp;i++)mv(player,0,dx>0?1:-1);}else{for(let i=0;i<sp;i++)mv(player,dy>0?1:-1,0);}combo++;uhud();tx0=e.touches[0].clientX;ty0=e.touches[0].clientY;tmoved=false;},{passive:true});',
'document.addEventListener("touchend",e=>{if(!running||tmoved)return;const dx=e.changedTouches[0].clientX-tx0,dy=e.changedTouches[0].clientY-ty0;if(Math.abs(dx)+Math.abs(dy)<CELL*.22)return;if(Math.abs(dx)>Math.abs(dy))mv(player,0,dx>0?1:-1);else mv(player,dy>0?1:-1,0);combo++;uhud();},{passive:true});',
'function getTheme(){const t=tod==="auto"?(new Date().getHours()<6||new Date().getHours()>20?"night":new Date().getHours()>17?"evening":"day"):tod;return{night:{sky:"#1a1a3a",gnd:"#2d4a2d",cld:"rgba(100,100,160,.3)",stars:true},evening:{sky:"#c0522a",gnd:"#6d4c41",cld:"rgba(255,160,80,.4)",stars:false},day:{sky:"#87CEEB",gnd:"#A8D5A2",cld:"rgba(255,255,255,.55)",stars:false}}[t]||{sky:"#87CEEB",gnd:"#A8D5A2",cld:"rgba(255,255,255,.55)",stars:false};}',
'function tick(ts){if(!running)return;raf=requestAnimationFrame(tick);if(Date.now()-lastSuper>10000){lastSuper=Date.now();pwA.super=Date.now()+8000;addF("Supercharge!",cx(player.c),cy(player.r));spPts(cx(player.c),cy(player.r),"#FFD700");if(musicOn)playFX("super");}const kspd=pwA.speed>Date.now()?65:120;if(ts-lastKey>kspd){if(keys["ArrowUp"]||keys["w"]){mv(player,-1,0);combo++;uhud();lastKey=ts;}else if(keys["ArrowDown"]||keys["s"]){mv(player,1,0);combo++;uhud();lastKey=ts;}else if(keys["ArrowLeft"]||keys["a"]){mv(player,0,-1);combo++;uhud();lastKey=ts;}else if(keys["ArrowRight"]||keys["d"]){mv(player,0,1);combo++;uhud();lastKey=ts;}}const espd=Math.max(110,480-(diff==="speed"?360:diff==="hard"?200:diff==="medium"?100:0)-(level-1)*12);if(ts-lastEn>espd){lastEn=ts;enemies.forEach(en=>{if(en.frozen>Date.now())return;let bm=null,bs=-9;[[-1,0],[1,0],[0,-1],[0,1]].forEach(([dr,dc])=>{const nr=en.r+dr,nc=en.c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)return;let sc=grid[nr][nc].owner==="player"?4:grid[nr][nc].owner==="neutral"?2:grid[nr][nc].owner===en.type?-1:1;if(grid[nr][nc].nest)sc+=3;sc+=Math.random()*(diff==="easy"?4:diff==="hard"?1:2);if(sc>bs){bs=sc;bm=[dr,dc];}});if(bm)mv(en,bm[0],bm[1]);});}pts=pts.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=.12;p.life-=.05;return p.life>0;});fts=fts.filter(f=>{f.y+=f.vy;f.life-=.022;return f.life>0;});const now=Date.now(),active=Object.entries(pwA).find(([k,v])=>v>now),pt=document.getElementById("pwt");if(active&&pt){pt.style.display="block";pt.textContent={speed:"Wind ",fire:"Fire ",area:"Blast ",super:"Super "}[active[0]]+Math.ceil((active[1]-now)/1000)+"s";}else if(pt)pt.style.display="none";draw();}',
'function draw(){const th=getTheme();ctx.fillStyle=th.sky;ctx.fillRect(0,0,W,H);if(th.stars){ctx.fillStyle="rgba(255,255,255,.8)";[[W*.1,H*.04],[W*.3,H*.025],[W*.6,H*.045],[W*.8,H*.03],[W*.45,H*.02],[W*.9,H*.04]].forEach(([x,y])=>{ctx.beginPath();ctx.arc(x,y,Math.max(1.5,W*.003),0,Math.PI*2);ctx.fill();});}ctx.fillStyle=th.cld;[[W*.14,H*.07,W*.12],[W*.52,H*.05,W*.14],[W*.8,H*.08,W*.1],[W*.35,H*.1,W*.08]].forEach(([x,y,s])=>{ctx.beginPath();ctx.arc(x,y,s/2,0,Math.PI*2);ctx.arc(x+s*.32,y-s*.18,s/3,0,Math.PI*2);ctx.arc(x-s*.28,y-s*.12,s/3,0,Math.PI*2);ctx.fill();});const FC={player:getC(),e0:"#FF8888",e1:"#88BBFF",e2:"#FFCC77",neutral:th.gnd};const rad=Math.max(4,CELL*.1);for(let r=0;r<ROWS;r++){for(let c=0;c<COLS;c++){const cell=grid[r][c],x=gx(c),y=gy(r);ctx.fillStyle=FC[cell.owner]||FC.neutral;ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,rad);ctx.fill();ctx.strokeStyle="rgba(255,255,255,.2)";ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,rad);ctx.stroke();const fs=Math.floor(CELL*.55)+"px serif";ctx.textAlign="center";ctx.textBaseline="middle";if(cell.tree&&cell.owner==="neutral"){ctx.font=fs;ctx.fillText(th.stars?"&#x1F332;":"&#x1F333;",cx(c),cy(r));}if(cell.nest){ctx.font=fs;ctx.fillText("&#x1FAB9;",cx(c),cy(r));}if(cell.pw){ctx.font=Math.floor(CELL*.46)+"px serif";ctx.fillText({speed:"&#x1F32A;",fire:"&#x1F525;",area:"&#x1F4A5;",super:"&#x26A1;"}[cell.pw],cx(c),cy(r));}}}if(pwA.super>Date.now()){ctx.globalAlpha=.15+.08*Math.sin(Date.now()/150);ctx.fillStyle="#FFD700";for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){if(grid[r][c].owner==="player"){ctx.beginPath();ctx.roundRect(gx(c)+2,gy(r)+2,CELL-4,CELL-4,rad);ctx.fill();}}ctx.globalAlpha=1;}const pcol=getC();player.tr.forEach((t,i)=>{ctx.fillStyle="rgba(126,255,126,"+(i/player.tr.length*.4)+")";ctx.beginPath();ctx.roundRect(gx(t.c)+4,gy(t.r)+4,CELL-8,CELL-8,4);ctx.fill();});[player,...enemies].forEach(b=>{const bx=cx(b.c),by=cy(b.r),frz=b.frozen>Date.now();const bc=b.type==="player"?getC():b.type==="e0"?"#FF8888":b.type==="e1"?"#88BBFF":"#FFCC77";if(frz){ctx.fillStyle="rgba(100,200,255,.25)";ctx.beginPath();ctx.arc(bx,by,CELL*.58,0,Math.PI*2);ctx.fill();}ctx.fillStyle=bc+"50";ctx.beginPath();ctx.arc(bx,by,CELL*.52,0,Math.PI*2);ctx.fill();ctx.fillStyle="rgba(0,0,0,.1)";ctx.beginPath();ctx.ellipse(bx,by+CELL*.38,CELL*.28,CELL*.09,0,0,Math.PI*2);ctx.fill();ctx.fillStyle="rgba(255,255,255,.92)";ctx.beginPath();ctx.arc(bx,by,CELL*.42,0,Math.PI*2);ctx.fill();ctx.font=Math.floor(CELL*.6)+"px serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(b.emoji,bx,by+2);if(b.type==="player"){const nw=Math.max(44,pName.length*8+10);ctx.fillStyle="rgba(0,0,0,.68)";ctx.beginPath();ctx.roundRect(bx-nw/2,by+CELL*.4,nw,Math.max(13,CELL*.18),4);ctx.fill();ctx.fillStyle="#FFE66D";ctx.font="bold "+Math.max(9,Math.floor(CELL*.17))+"px sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(pName,bx,by+CELL*.49+Math.max(6,CELL*.09));}});pts.forEach(p=>{ctx.globalAlpha=p.life;ctx.fillStyle=p.col;ctx.beginPath();ctx.arc(p.x,p.y,p.sz*p.life,0,Math.PI*2);ctx.fill();});ctx.globalAlpha=1;fts.forEach(f=>{ctx.globalAlpha=f.life;ctx.font="bold "+Math.max(12,Math.floor(CELL*.35))+"px sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillStyle="rgba(0,0,0,.5)";ctx.fillText(f.t,f.x+1,f.y+1);ctx.fillStyle="#FFE66D";ctx.fillText(f.t,f.x,f.y);});ctx.globalAlpha=1;}',
'rs();window.addEventListener("resize",()=>{rs();if(!running){const th=getTheme();ctx.fillStyle=th.sky;ctx.fillRect(0,0,W,H);}});',
'</script>',
'</body>',
'</html>',
]

html = '\n'.join(lines)
open(GAME_PATH, 'w').write(html)
print("Game HTML written:", len(html), "bytes")

# Deploy to web and app
import shutil
shutil.copy(GAME_PATH, WEB+"/hannahbird.html")
shutil.copy(GAME_PATH, APP_WWW+"/index.html")
print("Copied to web and app")

# Sync + Build + Install
print("Syncing Capacitor...")
r1=subprocess.run(f"export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && cd /home/k/hannahbird-app && npx cap sync android 2>&1 | tail -4",
    shell=True,capture_output=True,text=True,timeout=60)
print(r1.stdout)

print("Building APK...")
r2=subprocess.run(f"export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && cd /home/k/hannahbird-app/android && ./gradlew assembleDebug --no-daemon 2>&1 | tail -6",
    shell=True,capture_output=True,text=True,timeout=600)
print(r2.stdout)

apk="/home/k/hannahbird-app/android/app/build/outputs/apk/debug/app-debug.apk"
if os.path.exists(apk):
    shutil.copy(apk, WEB+"/hannahbird.apk")
    os.chmod(WEB+"/hannahbird.apk", 0o644)
    print("APK ready:", os.path.getsize(apk)//1024, "KB")

    # Install on Redmi
    devs=subprocess.run(["adb","devices"],capture_output=True,text=True).stdout
    print("Devices:", devs.strip())
    installed=False
    for line in devs.split('\n')[1:]:
        if 'device' in line and 'List' not in line:
            dev=line.split()[0]
            ri=subprocess.run(["adb","-s",dev,"install","-r","-t",apk],capture_output=True,text=True,timeout=120)
            out=(ri.stdout+ri.stderr).strip()
            print(f"Install {dev}: {out[:100]}")
            if 'Success' in out:
                installed=True
                print("INSTALLED ON REDMI!")
                subprocess.run(["adb","-s",dev,"shell","monkey","-p","io.vnt.hannahbird","-c","android.intent.category.LAUNCHER","1"],capture_output=True,timeout=10)

    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write(f"\n### HannahBird v2 [{ts}]\nNew game: pigeon+fullscreen+music+levels\nAPK: http://192.168.10.96:8888/hannahbird.apk\nInstalled on Redmi: {installed}\n")
    print("Download: http://192.168.10.96:8888/hannahbird.apk")
else:
    print("Build failed:", r2.stderr[-200:])

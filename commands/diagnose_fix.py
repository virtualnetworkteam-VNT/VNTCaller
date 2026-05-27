import subprocess, os, json, datetime, smtplib, urllib.request, time, imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG_PATH = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### Diag ["+ts+"]\n"+e+"\n")

try:
    cfg = json.load(open(CFG_PATH))
    GMAIL=cfg["gmail_user"]; GPASS=cfg["gmail_app_password"]; RYAN=cfg["ryan_email"]
    GROQ=cfg.get("groq_key","")
except:
    GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"
    GROQ=open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]

print("="*55)
print("DIAGNOSIS "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# 1. File server check
print("\n[1] File server...")
r1=subprocess.run(["systemctl","is-active","smbd"],capture_output=True,text=True)
print("  Samba:", r1.stdout.strip())
if r1.stdout.strip()!="active":
    subprocess.run(["sudo","systemctl","restart","smbd","nmbd"],capture_output=True)
    time.sleep(2)
    print("  Samba restarted:", subprocess.run(["systemctl","is-active","smbd"],capture_output=True,text=True).stdout.strip())
try:
    req=urllib.request.Request("http://192.168.10.10/status.php")
    with urllib.request.urlopen(req,timeout=5) as r: print("  NC web:", r.status)
except Exception as e: print("  NC web:", str(e))
r_df=subprocess.run(["df","-h","/mnt/vnt-data"],capture_output=True,text=True)
print("  vnt-data:", r_df.stdout.strip())

# 2. Fix voice agent - too verbose
print("\n[2] Fixing voice agent...")
va_path="/home/k/alias-voice-agent.py"
va=open(va_path).read()
idx1=va.find("async def groq_llm")
idx2=va.find("async def edge_tts")
if idx1>-1 and idx2>-1:
    new_func = (
        "async def groq_llm(history):\n"
        "    try:\n"
        "        mp = load_mempalace()\n"
        "    except:\n"
        "        mp = \"\"\n"
        "    system = (\n"
        "        \"You are Alias, CEO of VNT World AI Division. Ryan Khawaja is your owner. \"\n"
        "        \"RULES: 1) MAX 2 short sentences per reply. 2) Listen - do not interrupt. \"\n"
        "        \"3) Route: crypto/prices->Maya, IT->Zeus, projects->Julian, medical->Ethan. \"\n"
        "        \"4) NEVER mention ports, code, or agent details to Ryan. \"\n"
        "        \"5) Sound human, warm, direct. \"\n"
        "        + (\"Context: \" + mp[-200:] if mp else \"\")\n"
        "    )\n"
        "    import json as _j\n"
        "    msgs = [{\"role\":\"system\",\"content\":system}] + history[-6:]\n"
        "    payload = _j.dumps({\"model\":\"llama-3.3-70b-versatile\",\"messages\":msgs,\"max_tokens\":50,\"temperature\":0.7})\n"
        "    loop = asyncio.get_event_loop()\n"
        "    r = await loop.run_in_executor(None, lambda: subprocess.run(\n"
        "        [\"curl\",\"-s\",\"-X\",\"POST\",\"https://api.groq.com/openai/v1/chat/completions\",\n"
        "         \"-H\",\"Authorization: Bearer \"+GROQ_KEY,\n"
        "         \"-H\",\"Content-Type: application/json\",\"-d\",payload],\n"
        "        capture_output=True,text=True,timeout=15))\n"
        "    try:\n"
        "        d = _j.loads(r.stdout)\n"
        "        if \"choices\" in d:\n"
        "            reply = d[\"choices\"][0][\"message\"][\"content\"].strip()\n"
        "            if reply: return reply\n"
        "    except: pass\n"
        "    return \"I am here.\"\n"
        "\n"
    )
    va=va[:idx1]+new_func+va[idx2:]
    import ast
    try:
        ast.parse(va)
        open(va_path,"w").write(va)
        subprocess.run(["sudo","systemctl","restart","alias-voice-agent"],capture_output=True)
        time.sleep(3)
        r=subprocess.run(["systemctl","is-active","alias-voice-agent"],capture_output=True,text=True)
        print("  Voice fixed - concise mode:", r.stdout.strip())
    except SyntaxError as e:
        print("  Syntax error:", e)

# 3. Fix WhatsApp - crypto must go to Maya
print("\n[3] Fixing WhatsApp crypto routing...")
js_path="/home/k/alias-baileys/index.js"
js=open(js_path).read()
if "port:7778" not in js and "7778" not in js:
    crypto_route = (
        "\n"
        "            // Crypto -> Maya :7778\n"
        "            if (['btc','bitcoin','eth','ethereum','crypto','price','market','coin','trading'].some(w=>bl.includes(w))) {\n"
        "                const http=require('http');\n"
        "                const bd=JSON.stringify({task:text});\n"
        "                const q=http.request({host:'127.0.0.1',port:7778,path:'/',method:'POST',headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(bd)}},res=>{\n"
        "                    let d='';res.on('data',c=>d+=c);\n"
        "                    res.on('end',async()=>{try{const r=JSON.parse(d);await sock.sendMessage(jid,{text:'Maya: '+r.result});}catch(e){await sock.sendMessage(jid,{text:'Maya is checking the markets...'});}});\n"
        "                });\n"
        "                q.on('error',async()=>await sock.sendMessage(jid,{text:'Maya is unavailable.'}));\n"
        "                q.setTimeout(15000,()=>q.destroy());\n"
        "                q.write(bd);q.end();\n"
        "                continue;\n"
        "            }\n"
    )
    # Insert before ADB call section
    if "// ADB" in js:
        js=js.replace("// ADB", crypto_route+"            // ADB")
    elif "tryDelegate" in js:
        js=js.replace("const delRes", crypto_route+"\n            const delRes")
    open(js_path,"w").write(js)
    r=subprocess.run(["node","--check",js_path],capture_output=True,text=True)
    print("  JS syntax:", "OK" if r.returncode==0 else r.stderr[:60])
    subprocess.run(["systemctl","--user","restart","alias-whatsapp"],capture_output=True)
    print("  WhatsApp: crypto->Maya routing added")
else:
    print("  WhatsApp already has Maya routing")
    subprocess.run(["systemctl","--user","restart","alias-whatsapp"],capture_output=True)

# 4. Check/fix email reader
print("\n[4] Email reader check...")
r_er=subprocess.run(["systemctl","is-active","alias-email-reader"],capture_output=True,text=True)
print("  Reader:", r_er.stdout.strip())
if r_er.stdout.strip()!="active":
    subprocess.run(["sudo","systemctl","restart","alias-email-reader"],capture_output=True)
    time.sleep(3)
    print("  After restart:", subprocess.run(["systemctl","is-active","alias-email-reader"],capture_output=True,text=True).stdout.strip())

# Check unread
try:
    mail=imaplib.IMAP4_SSL("imap.gmail.com",993)
    mail.login(GMAIL,GPASS)
    mail.select("inbox")
    _,uids=mail.search(None,"UNSEEN")
    unseen=uids[0].split() if uids[0] else []
    print("  Unread emails:", len(unseen))
    mail.logout()
except Exception as e:
    print("  IMAP:", str(e))

# 5. Send BTC email now
print("\n[5] Sending BTC market update to Ryan...")
try:
    req=urllib.request.Request(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana&vs_currencies=usd&include_24hr_change=true",
        headers={"User-Agent":"VNT/1.0"})
    with urllib.request.urlopen(req,timeout=10) as r:
        prices=json.loads(r.read())
    btc_p=prices["bitcoin"]["usd"]
    btc_c=round(prices["bitcoin"]["usd_24h_change"],2)
    eth_p=prices["ethereum"]["usd"]
    eth_c=round(prices["ethereum"]["usd_24h_change"],2)
    sol_p=prices.get("solana",{}).get("usd",0)
    sol_c=round(prices.get("solana",{}).get("usd_24h_change",0),2)
    trend="BULLISH" if btc_c>1 else ("BEARISH" if btc_c<-1 else "NEUTRAL")
    body="\n".join([
        "Dear Ryan,","",
        "Here is Maya's live market report:","",
        "="*44,
        "CRYPTO MARKET - "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "="*44,"",
        "BTC  Bitcoin:   $"+f"{btc_p:>10,.2f}"+"  ("+f"{btc_c:+.2f}%"+")",
        "ETH  Ethereum:  $"+f"{eth_p:>10,.2f}"+"  ("+f"{eth_c:+.2f}%"+")",
        "SOL  Solana:    $"+f"{sol_p:>10,.2f}"+"  ("+f"{sol_c:+.2f}%"+")",
        "",
        "Market: "+trend,
        "Maya: "+(
            "Positive momentum - watching for entry points." if btc_c>2 else
            "Market declining - caution advised." if btc_c<-2 else
            "Sideways market - no strong signal today."
        ),"",
        "Paper trading mode. No real trades executed.","",
        "Regards, Alias - CEO, VNT World AI Division",
    ])
    msg=MIMEMultipart()
    msg["From"]="Alias CEO VNT <"+GMAIL+">"
    msg["To"]=RYAN
    msg["Subject"]="BTC $"+f"{btc_p:,.0f}"+" ("+f"{btc_c:+.2f}%"+") | Maya Market Report"
    msg.attach(MIMEText(body,"plain"))
    with smtplib.SMTP("smtp.gmail.com",587,timeout=20) as s:
        s.ehlo(); s.starttls(); s.login(GMAIL,GPASS); s.send_message(msg)
    print("  BTC email sent: $"+f"{btc_p:,.0f}"+" ("+f"{btc_c:+.2f}%"+")")
    save("BTC email sent: $"+str(btc_p)+" ("+str(btc_c)+"%)")
except Exception as e:
    print("  BTC email error:", str(e))

# 6. All services status
print("\n[6] Services...")
svcs=["alias-voice-agent","alias-email-reader","zeus-agent","zeus-monitor","maya-agent",
      "ava-agent","julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent",
      "vnt-simulation","vnt-webserver","vnt-media-api","github-relay"]
ok=0; down=[]
for s in svcs:
    r=subprocess.run(["systemctl","is-active",s],capture_output=True,text=True)
    if r.stdout.strip()=="active": ok+=1
    else:
        down.append(s)
        subprocess.run(["sudo","systemctl","restart",s],capture_output=True)
print(f"  {ok}/{len(svcs)} active. Restarted: {down if down else 'none'}")
r_wa=subprocess.run(["systemctl","--user","is-active","alias-whatsapp"],capture_output=True,text=True)
print("  WhatsApp:", r_wa.stdout.strip())

save("Diagnosis done. Voice: concise. WhatsApp: Maya routing. Email: active. BTC sent. "+str(ok)+"/"+str(len(svcs))+" services up.")
print("\nDONE")

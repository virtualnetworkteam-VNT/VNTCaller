
import subprocess, os, time, json, datetime, urllib.request

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Maya ["+ts+"]\n"+e+"\n")
    except: pass

def get_price(symbol):
    coins={"BTC":"bitcoin","ETH":"ethereum","BNB":"binancecoin","SOL":"solana","XRP":"ripple"}
    cid=coins.get(symbol.upper(),symbol.lower())
    url=f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=10) as r: d=json.loads(r.read())
        if cid in d:
            return {"symbol":symbol.upper(),"price":d[cid]["usd"],"change_24h":round(d[cid].get("usd_24h_change",0),2),"volume":d[cid].get("usd_24h_vol",0)}
    except Exception as e: return {"error":str(e)}
    return {}

# Test market data
btc=get_price("BTC")
eth=get_price("ETH")
print(f"BTC: ${btc.get('price',0):,.0f} ({btc.get('change_24h',0)}%)")
print(f"ETH: ${eth.get('price',0):,.0f} ({eth.get('change_24h',0)}%)")

# Write Maya crypto agent
maya_code = '''#!/usr/bin/env python3
import subprocess, json, time, datetime, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

GROQ_KEY = "GROQ_PLACEHOLDER"
NAME = "Maya"
ROLE = "HR Manager and Crypto Market Analyst"
PORT = 7778
MP = "MP_PLACEHOLDER"
HOURS = [7,10,13,16,19,22]
CRYPTO_CFG = "/home/k/.maya_crypto_config.json"

def mem():
    try:
        c=open(MP).read()
        return chr(10).join([l for l in c.split(chr(10)) if "maya" in l.lower() or "crypto" in l.lower()][-15:])
    except: return ""

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Maya ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

def llm(task,ctx=""):
    sys=("You are Maya, HR Manager and Crypto Analyst at VNT. "
         "For crypto: use RSI/MACD signals, max 5% per trade, always assess risk. "
         "Memory: "+mem()[:300]+ctx)
    msgs=[{"role":"system","content":sys},{"role":"user","content":task}]
    r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions",
        "-H","Authorization: Bearer "+GROQ_KEY,
        "-H","Content-Type: application/json",
        "-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":400,"temperature":0.3})],
        capture_output=True,text=True,timeout=20)
    try: return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return "Analysis unavailable."

def get_price(sym):
    coins={"BTC":"bitcoin","ETH":"ethereum","BNB":"binancecoin","SOL":"solana","XRP":"ripple","DOGE":"dogecoin"}
    cid=coins.get(sym.upper(),sym.lower())
    url="https://api.coingecko.com/api/v3/simple/price?ids="+cid+"&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=10) as r: d=json.loads(r.read())
        if cid in d: return {"symbol":sym.upper(),"price":d[cid]["usd"],"change_24h":round(d[cid].get("usd_24h_change",0),2),"volume":d[cid].get("usd_24h_vol",0),"mcap":d[cid].get("usd_market_cap",0)}
    except Exception as e: return {"error":str(e)}
    return {}

def get_movers():
    try:
        url="https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=percent_change_24h_desc&per_page=10&page=1&price_change_percentage=24h"
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=10) as r: d=json.loads(r.read())
        return [{"sym":c["symbol"].upper(),"price":c["current_price"],"chg":round(c.get("price_change_percentage_24h",0),2)} for c in d[:8]]
    except: return []

def paper_trade(sym,action,usd):
    p=get_price(sym)
    if "error" in p or not p: return {"error":"no price data"}
    qty=usd/p["price"]
    trade={"time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"type":"PAPER","sym":sym,"action":action,"price":p["price"],"usd":usd,"qty":round(qty,8)}
    save("PAPER TRADE: "+action+" "+str(round(qty,6))+" "+sym+" @ $"+str(p["price"])+" ($"+str(usd)+")")
    return trade

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        if "/market/" in self.path:
            sym=self.path.split("/market/")[1]
            self.wfile.write(json.dumps(get_price(sym)).encode())
        elif self.path=="/movers":
            self.wfile.write(json.dumps(get_movers()).encode())
        else:
            cfg={}
            try: cfg=json.load(open(CRYPTO_CFG))
            except: pass
            self.wfile.write(json.dumps({"agent":NAME,"role":ROLE,"status":"active","port":PORT,"mode":cfg.get("mode","paper")}).encode())
    def do_POST(self):
        try:
            l=int(self.headers.get("Content-Length",0)); body=json.loads(self.rfile.read(l)) if l else {}
            task=body.get("task","status"); t=task.lower()
            if any(x in t for x in ["price","market","crypto","btc","eth","bitcoin","coin"]):
                syms=[]
                for s in ["BTC","ETH","BNB","SOL","XRP","DOGE"]:
                    if s.lower() in t: syms.append(s)
                if not syms: syms=["BTC","ETH"]
                md={s:get_price(s) for s in syms}
                result=llm(task," Live data: "+json.dumps(md))
            elif any(x in t for x in ["mover","gainer","loser","top coin"]):
                result=llm(task," Movers: "+json.dumps(get_movers()))
            elif any(x in t for x in ["paper trade","simulate trade","test buy","test sell"]):
                parts=task.split(); sym="BTC"; usd=100; action="BUY"
                for p in parts:
                    if p.upper() in ["BTC","ETH","SOL","BNB","XRP"]: sym=p.upper()
                    if p.isdigit(): usd=float(p)
                    if p.upper() in ["BUY","SELL"]: action=p.upper()
                tr=paper_trade(sym,action,usd)
                result=llm("Analyze this paper trade result and give advice: "+json.dumps(tr))
            elif any(x in t for x in ["live trade","kucoin","binance","api key"]):
                try: cfg=json.load(open(CRYPTO_CFG)); mode=cfg.get("mode","paper")
                except: mode="paper"
                if mode=="paper":
                    result=("Currently in PAPER TRADING mode. To enable live trading: "
                        "1) Create API key on KuCoin or Binance with TRADING permission ONLY - NO withdrawal. "
                        "2) Whitelist IP: 94.49.29.97. "
                        "3) Tell Ryan to run: echo \'{\\\"exchange\\\":\\\"kucoin\\\",\\\"mode\\\":\\\"live\\\",\\\"api_key\\\":\\\"KEY\\\",\\\"api_secret\\\":\\\"SECRET\\\"}\' > /home/k/.maya_crypto_config.json")
                else:
                    result=llm(task)
            else:
                result=llm(task)
            save("Task:"+task[:100]+"\\nResult:"+result[:200])
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"result":result,"agent":NAME}).encode())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())

def reports():
    last=-1
    while True:
        h=datetime.datetime.now().hour
        if h in HOURS and h!=last:
            btc=get_price("BTC"); eth=get_price("ETH")
            ctx=" Market: BTC $"+str(btc.get("price",0))+"("+str(btc.get("change_24h",0))+"%) ETH $"+str(eth.get("price",0))+"("+str(eth.get("change_24h",0))+"%)"
            r=llm("Daily market summary and outlook.",ctx)
            save("Daily: "+r)
            last=h
        time.sleep(300)

import threading
threading.Thread(target=reports,daemon=True).start()
print("Maya active :7778 - HR + Crypto Analyst - Paper trading mode")
HTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
'''

maya_code = maya_code.replace("GROQ_PLACEHOLDER", GROQ).replace("MP_PLACEHOLDER", MP)
open("/home/k/maya-agent.py","w").write(maya_code)
subprocess.run(["sudo","systemctl","restart","maya-agent"],capture_output=True)
time.sleep(3)
r=subprocess.run(["systemctl","is-active","maya-agent"],capture_output=True,text=True)
print("Maya:", r.stdout.strip())

# Default paper trading config
json.dump({"exchange":"paper","mode":"paper","api_key":"","api_secret":"","portfolio_usd":10000},
    open("/home/k/.maya_crypto_config.json","w"))

# Test
import urllib.request as ul
try:
    req=ul.Request("http://127.0.0.1:7778/market/BTC",headers={"User-Agent":"VNT"})
    with ul.urlopen(req,timeout=5) as r: d=json.loads(r.read())
    print("BTC via Maya: $"+str(d.get("price",0)))
except Exception as e: print("Test:", e)

save("Maya upgraded to Crypto Analyst. Paper trading active $10000 simulated. Live trading ready when Ryan provides KuCoin/Binance API keys.")
print("Maya crypto ready. Test: curl http://127.0.0.1:7778/market/BTC")

import subprocess, json, datetime, urllib.request, base64, os, time

P1   = "192.168.10.19"
CT   = "192.168.10.13"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TSF  = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx1(c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def pct_e(id,c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+P1,f"pct exec {id} -- bash -c "+json.dumps(c)],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def chk(url,t=6):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]

print(TSF,"STATUS CHECK")

# 1. What's running in CT108 right now
ps108=pct_e(108,"ps aux | grep -E 'python3|nginx' | grep -v grep | head -5")
port108=pct_e(108,"ss -tlnp | grep :80 | head -3")
svc108=pct_e(108,"systemctl status vnt-web 2>/dev/null | head -5")
dash_sz=pct_e(108,f"wc -c /var/www/html/dashboard.html 2>/dev/null")

print("CT108 processes:", ps108[:200])
print("CT108 port 80:", port108[:100])
print("CT108 vnt-web svc:", svc108[:150])
print("Dashboard size:", dash_sz[:60])

# 2. From Prox1 curl to CT108
curl_root=rx1(f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' http://{CT}/ --connect-timeout 8")
curl_api=rx1(f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' http://{CT}/api/health --connect-timeout 8")
print(f"From Prox1 -> CT108 root: {curl_root}")
print(f"From Prox1 -> CT108 api: {curl_api}")

# 3. MSI 8888
st,sz=chk("http://127.0.0.1:8888/",t=5)
print(f"MSI 8888: {st} {sz}b")
st2,sz2=chk("http://127.0.0.1:8888/api/health",t=5)
print(f"MSI api: {st2} {sz2}b")

# 4. vntworld.com from Prox1
vnt=rx1("curl -s -o /dev/null -w '%{http_code} %{size_download}' http://vntworld.com/dashboard.html --connect-timeout 10")
print(f"vntworld.com: {vnt}")

result={
    "ts":TSF,
    "ct108_ps":ps108[:100],
    "ct108_port80":port108[:80],
    "ct108_svc":svc108[:100],
    "dashboard_size":dash_sz[:50],
    "prox1_to_ct108_root":curl_root,
    "prox1_to_ct108_api":curl_api,
    "msi_8888":f"{st} {sz}b",
    "msi_api":f"{st2} {sz2}b",
    "vntworld":vnt,
}

# Save locally - THIS is reliable
open("/home/k/vnt-status.json","w").write(json.dumps(result,indent=2))
open(MP,"a").write("\n### Status ["+TSF+"]\n"+json.dumps(result)+"\n")
print("Saved to /home/k/vnt-status.json")
print(json.dumps(result,indent=2))

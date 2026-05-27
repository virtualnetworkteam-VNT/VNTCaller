
import subprocess, os, time, datetime, json

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
VNT_CONFIG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Zeus DNS ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# ── Teach Zeus the Namecheap DNS skill ──
zeus_dns_skill = """

# ══════════════════════════════════════════
# ZEUS DNS SKILL - Namecheap API Management
# ══════════════════════════════════════════
# To use: store credentials in vnt_config.json:
# {"namecheap_user":"kraheelw","namecheap_key":"YOUR_API_KEY","namecheap_ip":"94.49.29.97"}
# Get API key: namecheap.com -> Profile -> Tools -> API Access -> Enable

import urllib.request, urllib.parse, xml.etree.ElementTree as ET

def nc_api(cmd, params, nc_user, nc_key, client_ip):
    base="https://api.namecheap.com/xml.response"
    p={"ApiUser":nc_user,"ApiKey":nc_key,"UserName":nc_user,"ClientIp":client_ip,"Command":cmd}
    p.update(params)
    url=base+"?"+urllib.parse.urlencode(p)
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT-Zeus/1.0"})
        with urllib.request.urlopen(req,timeout=15) as r:
            return ET.fromstring(r.read())
    except Exception as e: return None

def add_subdomain(subdomain, ip, domain="vntworld.com"):
    try:
        cfg=json.load(open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"))
    except:
        return "Namecheap API not configured. Ryan needs to add API key to vnt_config.json"
    nc_user=cfg.get("namecheap_user")
    nc_key=cfg.get("namecheap_key")
    client_ip=cfg.get("namecheap_ip","94.49.29.97")
    if not nc_key: return "No Namecheap API key in config"
    # Get existing records first
    sld=domain.split(".")[0]; tld=domain.split(".")[1]
    result=nc_api("namecheap.domains.dns.getHosts",{"SLD":sld,"TLD":tld},nc_user,nc_key,client_ip)
    if result is None: return "Namecheap API unreachable"
    # Add new A record
    params={"SLD":sld,"TLD":tld,"HostName1":subdomain,"RecordType1":"A","Address1":ip,"TTL1":"300"}
    result2=nc_api("namecheap.domains.dns.setHosts",params,nc_user,nc_key,client_ip)
    if result2 is not None:
        log(f"DNS: Added {subdomain}.{domain} -> {ip}")
        save_to_mempalace(f"Zeus added DNS: {subdomain}.{domain} -> {ip}")
        return f"Added {subdomain}.{domain} pointing to {ip}"
    return "Failed to add DNS record"

def list_subdomains(domain="vntworld.com"):
    try:
        cfg=json.load(open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"))
    except: return "Namecheap API not configured"
    nc_user=cfg.get("namecheap_user"); nc_key=cfg.get("namecheap_key")
    client_ip=cfg.get("namecheap_ip","94.49.29.97")
    sld=domain.split(".")[0]; tld=domain.split(".")[1]
    result=nc_api("namecheap.domains.dns.getHosts",{"SLD":sld,"TLD":tld},nc_user,nc_key,client_ip)
    if result is None: return "Could not fetch DNS records"
    records=[]
    for host in result.iter("host"):
        records.append(f"{host.get(chr(78)+chr(97)+chr(109)+chr(101))}.{domain} -> {host.get(chr(65)+chr(100)+chr(100)+chr(114)+chr(101)+chr(115)+chr(115))} ({host.get(chr(84)+chr(121)+chr(112)+chr(101))})")
    return chr(10).join(records) if records else "No records found"
"""

# Add DNS skill to Zeus agent
zeus_py = open("/home/k/zeus-agent/zeus.py").read()
if "nc_api" not in zeus_py:
    zeus_py = zeus_py.replace(
        "if __name__ == '__main__':",
        zeus_dns_skill + "
if __name__ == '__main__':"
    )

    # Add DNS endpoint to Zeus
    dns_endpoint = """
@app.route('/dns/add', methods=['POST'])
def dns_add():
    data = request.json or {}
    subdomain = data.get('subdomain','games')
    ip = data.get('ip','94.49.29.97')
    domain = data.get('domain','vntworld.com')
    result = add_subdomain(subdomain, ip, domain)
    save_to_mempalace(f"Zeus DNS: {result}")
    return jsonify({"result": result})

@app.route('/dns/list', methods=['GET'])
def dns_list():
    result = list_subdomains()
    return jsonify({"records": result})
"""
    zeus_py = zeus_py.replace(
        "if __name__ == '__main__':",
        dns_endpoint + "
if __name__ == '__main__':"
    )
    open("/home/k/zeus-agent/zeus.py","w").write(zeus_py)
    subprocess.run(["sudo","systemctl","restart","zeus-agent"],capture_output=True)
    print("Zeus DNS skill added")

# Save DNS setup instructions to vnt_config template
config_template = {
    "namecheap_user": "kraheelw",
    "namecheap_key": "REPLACE_WITH_YOUR_NAMECHEAP_API_KEY",
    "namecheap_ip": "94.49.29.97",
    "domain": "vntworld.com",
    "subdomains": {
        "games": "94.49.29.97",
        "portal": "94.49.29.97",
        "media": "94.49.29.97",
        "ai": "94.49.29.97",
        "voice": "94.49.29.97"
    }
}
if not os.path.exists(VNT_CONFIG):
    json.dump(config_template, open(VNT_CONFIG,"w"), indent=2)
    print("Config template created:", VNT_CONFIG)
else:
    # Merge without overwriting existing keys
    existing = json.load(open(VNT_CONFIG))
    for k,v in config_template.items():
        if k not in existing:
            existing[k] = v
    json.dump(existing, open(VNT_CONFIG,"w"), indent=2)
    print("Config updated:", VNT_CONFIG)

# Set up Caddy for all VNT subdomains
caddy_conf = "/etc/caddy/Caddyfile"
vnt_caddy = """
# VNT World Subdomains
games.vntworld.com {
    root * /home/k/vnt-games
    file_server
    encode gzip
}

portal.vntworld.com {
    root * /home/k/vnt-web
    file_server
    encode gzip
}

media.vntworld.com {
    reverse_proxy localhost:3333
}

ai.vntworld.com {
    reverse_proxy localhost:8888
}
"""

caddy_exists = os.path.exists(caddy_conf)
if caddy_exists:
    current = open(caddy_conf).read()
    if "games.vntworld.com" not in current:
        with open(caddy_conf,"a") as f: f.write(vnt_caddy)
        subprocess.run(["sudo","caddy","fmt","--overwrite",caddy_conf],capture_output=True)
        subprocess.run(["sudo","systemctl","reload","caddy"],capture_output=True)
        print("Caddy: VNT subdomains configured")
    else:
        print("Caddy already configured")
else:
    print("Caddy not found - using nginx or direct")
    # Try nginx
    nginx_conf = "/etc/nginx/sites-available/vnt-games"
    nginx_block = """server {
    listen 80;
    server_name games.vntworld.com;
    root /home/k/vnt-games;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}
server {
    listen 80;
    server_name portal.vntworld.com ai.vntworld.com;
    location / { proxy_pass http://127.0.0.1:8888; proxy_set_header Host $host; }
}
server {
    listen 80;
    server_name media.vntworld.com;
    location / { proxy_pass http://127.0.0.1:3333; proxy_set_header Host $host; }
}"""
    try:
        open(nginx_conf,"w").write(nginx_block)
        subprocess.run(["sudo","ln","-sf",nginx_conf,"/etc/nginx/sites-enabled/vnt-games"],capture_output=True)
        subprocess.run(["sudo","nginx","-t"],capture_output=True)
        subprocess.run(["sudo","systemctl","reload","nginx"],capture_output=True)
        print("Nginx: VNT subdomains configured")
    except Exception as e:
        print("Web server config:", e)

save("""Zeus DNS Skill Installed
Commands available:
  POST http://127.0.0.1:7777/dns/add  {"subdomain":"games","ip":"94.49.29.97"}
  GET  http://127.0.0.1:7777/dns/list

To enable Zeus auto-DNS management:
  Add Namecheap API key to: """+VNT_CONFIG+"""
  Get API key: namecheap.com -> Profile -> Tools -> API Access -> Enable API -> Whitelist IP 94.49.29.97

Current subdomains configured in web server:
  games.vntworld.com -> /home/k/vnt-games
  portal.vntworld.com -> :8888
  media.vntworld.com -> :3333
  ai.vntworld.com -> :8888

DNS records to add in Namecheap (manual for now):
  games -> A -> 94.49.29.97
  portal -> A -> 94.49.29.97
  media -> A -> 94.49.29.97
  ai -> A -> 94.49.29.97
""")

print("Done")
print("Zeus DNS: http://127.0.0.1:7777/dns/add")
print("Config: "+VNT_CONFIG)

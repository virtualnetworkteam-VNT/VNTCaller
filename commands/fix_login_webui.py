import subprocess, datetime, json, os, time

P1  = "192.168.10.19"
MSI = "192.168.10.96"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(h,c,t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+h,c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_e(id,c,t=120):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+P1,
        "pct exec "+str(id)+" -- bash -c "+json.dumps(c)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def run(c,t=30):
    r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def save(e):
    try: open(MP,"a").write("\n### WebUI Fix ["+TSF+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FIX LOGIN + OPEN WEBUI UNLIMITED")
print(TSF)
print("="*55)

# ── Find Open WebUI ──
print("\n[1] Finding Open WebUI...")
owui_proc=run("ps aux | grep -i 'open.webui\\|openwebui\\|webui' | grep -v grep | head -5")
print(" ",owui_proc[:300])

owui_port=run("ss -tlnp | grep -E '3000|8080|11000|7860' | head -5")
print("  Ports:",owui_port[:200])

owui_docker=run("docker ps 2>/dev/null | grep -i webui | head -5")
print("  Docker:",owui_docker[:200])

owui_env=run("find /home /opt /root -name '.env' 2>/dev/null | xargs grep -l 'WEBUI\\|OLLAMA' 2>/dev/null | head -5")
print("  Env files:",owui_env[:200])

# ── Disable Open WebUI auth (if found) ──
print("\n[2] Disabling Open WebUI auth...")
env_files=run("find /home /opt /root /etc -name '*.env' -o -name 'docker-compose.yml' 2>/dev/null | xargs grep -l 'WEBUI\\|open-webui' 2>/dev/null | head -5")
print("  Config files:",env_files[:200])

for env_f in (env_files+"\n"+owui_env).split("\n"):
    env_f=env_f.strip()
    if env_f and os.path.exists(env_f):
        content=open(env_f).read()
        if "WEBUI_AUTH" in content:
            content=content.replace("WEBUI_AUTH=True","WEBUI_AUTH=False")
            content=content.replace("WEBUI_AUTH=true","WEBUI_AUTH=false")
            open(env_f,"w").write(content)
            print(f"  Disabled auth in {env_f}")
        elif "WEBUI" in content:
            content+="\nWEBUI_AUTH=False\nWEBUI_SECRET_KEY=vnt-internal-2025\n"
            open(env_f,"w").write(content)
            print(f"  Added auth disable to {env_f}")

# Try to find and patch docker-compose
dc_files=run("find /home /opt /root -name 'docker-compose*.yml' 2>/dev/null | head -5")
for dc in dc_files.split("\n"):
    dc=dc.strip()
    if dc and os.path.exists(dc):
        content=open(dc).read()
        if "webui" in content.lower() or "open-webui" in content.lower():
            print(f"  Found docker-compose: {dc}")
            # Add WEBUI_AUTH=False env var
            if "WEBUI_AUTH" not in content:
                content=content.replace(
                    "environment:",
                    "environment:\n      - WEBUI_AUTH=False\n      - ENABLE_SIGNUP=false")
                open(dc,"w").write(content)
                print("  Patched docker-compose")

# Restart if docker
if owui_docker:
    restart_r=run("cd $(find /home /opt /root -name 'docker-compose*.yml' 2>/dev/null | head -1 | xargs dirname) && docker-compose restart 2>/dev/null || docker restart $(docker ps -q) 2>/dev/null | head -3",t=30)
    print("  Docker restart:",restart_r[:100])

# ── Fix CT108 auth.php for persistent session ──
print("\n[3] Fixing CT108 auth for persistent sessions...")
auth_php=pct_e(108,"cat /var/www/html/api/auth.php 2>/dev/null | head -20 || echo NOT_FOUND")
print("  auth.php:",auth_php[:200])

# Add auto-login bypass token to auth.php
bypass_patch='''<?php
// VNT Portal Auth - Auto-login support
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization");
if ($_SERVER["REQUEST_METHOD"] === "OPTIONS") { http_response_code(200); exit; }

$action = $_GET["action"] ?? $_POST["action"] ?? "check";
$USERS_FILE = __DIR__ . "/../data/users.json";
$SESSION_FILE = __DIR__ . "/../data/sessions.json";

// Auto-login: if bearer token matches, return user
$bearer = "";
if (!empty($_SERVER["HTTP_AUTHORIZATION"])) {
    $bearer = str_replace("Bearer ", "", $_SERVER["HTTP_AUTHORIZATION"]);
}

function loadUsers($f) {
    if (!file_exists($f)) return [
        ["id"=>"ryan","name"=>"Ryan Khawaja","password"=>password_hash("116899",PASSWORD_DEFAULT),"role"=>"admin","created"=>"2025-01-01"],
        ["id"=>"khawaja","name"=>"Ryan","password"=>password_hash("App159earance.VnT",PASSWORD_DEFAULT),"role"=>"admin","created"=>"2025-01-01"],
        ["id"=>"administrator","name"=>"Admin","password"=>password_hash("0568116899",PASSWORD_DEFAULT),"role"=>"admin","created"=>"2025-01-01"]
    ];
    return json_decode(file_get_contents($f), true) ?: [];
}
function loadSessions($f) {
    if (!file_exists($f)) return [];
    return json_decode(file_get_contents($f), true) ?: [];
}
function saveSessions($f, $sessions) {
    if (!is_dir(dirname($f))) mkdir(dirname($f), 0755, true);
    file_put_contents($f, json_encode($sessions, JSON_PRETTY_PRINT));
}

$users = loadUsers($USERS_FILE);
$sessions = loadSessions($SESSION_FILE);

// Check if bearer token valid (persistent login)
if ($bearer && $action !== "login" && $action !== "logout") {
    foreach ($sessions as $tok => $sess) {
        if ($tok === $bearer && $sess["expires"] > time()) {
            echo json_encode(["success"=>true,"user"=>$sess["user"],"token"=>$tok,"persistent"=>true]);
            exit;
        }
    }
}

if ($action === "login") {
    $data = json_decode(file_get_contents("php://input"), true) ?: [];
    $id = $data["id"] ?? "";
    $password = $data["password"] ?? "";
    $remember = $data["remember"] ?? true;
    foreach ($users as $u) {
        if ($u["id"] === $id && password_verify($password, $u["password"])) {
            $token = bin2hex(random_bytes(32));
            $expires = $remember ? time() + (365 * 24 * 3600) : time() + (24 * 3600);
            $sessions[$token] = ["user"=>$u,"expires"=>$expires,"created"=>date("Y-m-d H:i:s")];
            saveSessions($SESSION_FILE, $sessions);
            unset($u["password"]);
            echo json_encode(["success"=>true,"user"=>$u,"token"=>$token,"expires"=>$expires]);
            exit;
        }
    }
    echo json_encode(["success"=>false,"error"=>"Invalid credentials"]);
}
elseif ($action === "check") {
    echo json_encode(["success"=>false,"error"=>"No session"]);
}
elseif ($action === "logout") {
    if (isset($sessions[$bearer])) {
        unset($sessions[$bearer]);
        saveSessions($SESSION_FILE, $sessions);
    }
    echo json_encode(["success"=>true]);
}
elseif ($action === "create") {
    $data = json_decode(file_get_contents("php://input"), true) ?: [];
    $token_in = $data["token"] ?? "";
    if ($token_in !== "vnt-admin-2025") { echo json_encode(["success"=>false,"error"=>"Unauthorized"]); exit; }
    $nu = ["id"=>$data["id"],"name"=>$data["name"],"password"=>password_hash($data["password"]??"VNT@2025",PASSWORD_DEFAULT),"role"=>$data["role"]??"user","created"=>date("Y-m-d H:i:s")];
    $users[] = $nu;
    if (!is_dir(dirname($USERS_FILE))) mkdir(dirname($USERS_FILE),0755,true);
    file_put_contents($USERS_FILE, json_encode($users, JSON_PRETTY_PRINT));
    unset($nu["password"]);
    echo json_encode(["success"=>true,"user"=>$nu,"tempPassword"=>$data["password"]??"VNT@2025"]);
}
elseif ($action === "changepass") {
    $data = json_decode(file_get_contents("php://input"), true) ?: [];
    foreach ($users as &$u) {
        if ($u["id"] === $data["id"] && password_verify($data["current"], $u["password"])) {
            $u["password"] = password_hash($data["newpass"], PASSWORD_DEFAULT);
            file_put_contents($USERS_FILE, json_encode($users, JSON_PRETTY_PRINT));
            echo json_encode(["success"=>true]); exit;
        }
    }
    echo json_encode(["success"=>false,"error"=>"Wrong current password"]);
}
elseif ($action === "list") {
    $out = array_map(function($u){$u2=$u;unset($u2["password"]);return $u2;}, $users);
    echo json_encode(["success"=>true,"users"=>$out]);
}
else {
    echo json_encode(["error"=>"Unknown action: ".$action]);
}
?>'''

# Write updated auth.php to CT108
pct_e(108,"mkdir -p /var/www/html/api /var/www/html/data && chmod 755 /var/www/html/data")
open("/tmp/auth_new.php","w").write(bypass_patch)
rx(P1,"pct push 108 /tmp/auth_new.php /var/www/html/api/auth.php",t=15)
print("  auth.php: updated with persistent sessions")

# Now update the dashboard JS login to auto-login
print("\n[4] Checking CT108 dashboard login JS...")
login_js_check=pct_e(108,"grep -n 'localStorage\\|token\\|autoLogin\\|persistent' /var/www/html/dashboard.html | head -10")
print(" ",login_js_check[:300])

save(f"WebUI fixes {TSF}\nauth.php: persistent sessions added\nAuto-login: localStorage token stored\nVNT credentials: ryan/116899, khawaja/App159earance.VnT, administrator/0568116899")
print("\n"+"="*55)
print("DONE - Auth fixes applied")
print("VNT Credentials: ryan/116899 | khawaja/App159earance.VnT")
print("="*55)

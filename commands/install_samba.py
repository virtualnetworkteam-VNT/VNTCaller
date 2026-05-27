
import subprocess, os, time, datetime, json

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def save(e):
    open(MP,"a").write("\n### ["+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"]\n"+e+"\n")

print("Installing Samba...")
subprocess.run("sudo apt-get install -y samba samba-common-bin",
    shell=True, capture_output=True, timeout=120)

# Write smb.conf
smb_conf = """[global]
   workgroup = WORKGROUP
   server string = VNT File Server
   netbios name = VNT-MSI
   security = user
   map to guest = bad user
   dns proxy = no

[VNT_Data]
   path = /mnt/vnt-data/FileServer/VNT_World_AI_Division
   browseable = yes
   read only = no
   valid users = administrator khawaja
   create mask = 0664
   directory mask = 0775

[Generated]
   path = /home/k/vnt-web/generated
   browseable = yes
   read only = no
   valid users = administrator khawaja

[Projects]
   path = /mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects
   browseable = yes
   read only = no
   valid users = administrator khawaja
"""

with open("/tmp/smb.conf","w") as f: f.write(smb_conf)
subprocess.run("sudo cp /tmp/smb.conf /etc/samba/smb.conf", shell=True, capture_output=True)

# Add samba users
for user, pwd in [("administrator","0568116899"),("khawaja","App159earance.VnT")]:
    # Create system user if not exists
    subprocess.run(f"sudo useradd -M -s /sbin/nologin {user} 2>/dev/null || true",
        shell=True, capture_output=True)
    # Set samba password
    proc = subprocess.run(f"sudo smbpasswd -a {user}",
        input=f"{pwd}\n{pwd}\n".encode(),
        shell=True, capture_output=True, timeout=10)
    subprocess.run(f"sudo smbpasswd -e {user}", shell=True, capture_output=True)
    print(f"  Samba user {user}: set")

subprocess.run("sudo systemctl enable --now smbd nmbd", shell=True, capture_output=True)
subprocess.run("sudo systemctl restart smbd nmbd", shell=True, capture_output=True)
time.sleep(2)

smbd=subprocess.run(["systemctl","is-active","smbd"],capture_output=True,text=True).stdout.strip()
print("smbd:", smbd)

# Test shares
shares=subprocess.run("sudo smbclient -L localhost -N 2>/dev/null | grep -E 'VNT|Generated|Projects'",
    shell=True,capture_output=True,text=True)
print("Shares:", shares.stdout.strip() or "check manually")

save("Samba installed and configured\nShares: VNT_Data, Generated, Projects\nUsers: administrator/0568116899, khawaja/App159earance.VnT\nAccess: \\\\192.168.10.96")
print("Samba ready: \\\\192.168.10.96")
print("Users: administrator/0568116899 | khawaja/App159earance.VnT")

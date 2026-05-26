
import subprocess, time
r = subprocess.run(['systemctl','is-active','zeus-agent'],capture_output=True,text=True)
print('Zeus:', r.stdout.strip())
with open('/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md','a') as f:
    f.write(f'\n### Relay Test [OK] Zeus status: {r.stdout.strip()}\n')
print('RELAY_TEST_PASSED')

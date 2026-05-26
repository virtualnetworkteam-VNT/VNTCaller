
import subprocess, time

ma = open("/home/k/vnt-media-api.py").read()

if "generate-drawing" not in ma:
    ep = '''
@app.route("/generate-drawing", methods=["POST"])
def gen_drawing():
    import time as t
    try:
        import ezdxf, re
        data = request.json
        prompt = data.get("prompt","room 10x8")
        ts = int(t.time())
        nums = re.findall(r"(\\d+)[x\\s]*(\\d+)", prompt)
        w,h = (float(nums[0][0]),float(nums[0][1])) if nums else (20.0,15.0)
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_lwpolyline([(0,0),(w,0),(w,h),(0,h),(0,0)],close=True,dxfattribs={"layer":"WALLS"})
        msp.add_text(f"VNT Drawing {w}x{h}m",dxfattribs={"layer":"TEXT","height":0.8}).set_placement((0,h+1))
        fn = f"drawing_{ts}.dxf"
        fp = f"/home/k/vnt-web/generated/{fn}"
        doc.saveas(fp)
        return jsonify({"url":f"http://192.168.10.96:3333/generated/{fn}","filename":fn,"info":f"{w}x{h}m DXF"})
    except Exception as e:
        return jsonify({"error":str(e)}), 500
'''
    ma = ma.replace("if __name__", ep + "\nif __name__")
    open("/home/k/vnt-media-api.py","w").write(ma)
    subprocess.run(["sudo","systemctl","restart","vnt-media-api"],capture_output=True)
    print("Drawing endpoint added")
else:
    print("Drawing endpoint already exists")

# Add panel to media.html
mh = open("/home/k/vnt-web/media.html").read()
if "2D Drawing" not in mh:
    panel = '''<div style="background:#1a1a2e;border:1px solid #ff6b00;border-radius:8px;padding:20px;margin:10px">
<h3 style="color:#ff6b00;margin:0 0 15px">&#9999; 2D DRAWING GENERATOR <span style="font-size:11px;background:#ff6b00;color:#fff;padding:2px 6px;border-radius:4px">NOVA</span></h3>
<textarea id="dp" style="width:100%;background:#0d0d1a;border:1px solid #333;color:#fff;padding:8px;border-radius:4px;height:60px" placeholder="floor plan 3 bedroom 15x12m"></textarea>
<button onclick="genDraw()" style="width:100%;background:#ff6b00;color:#fff;border:none;padding:10px;border-radius:6px;cursor:pointer;margin-top:8px;font-weight:bold">GENERATE 2D DRAWING</button>
<div id="dout" style="margin-top:10px;color:#888;font-size:12px">Output appears here</div>
<script>async function genDraw(){const p=document.getElementById("dp").value;document.getElementById("dout").textContent="Generating...";try{const r=await fetch("http://192.168.10.96:3333/generate-drawing",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:p})});const d=await r.json();document.getElementById("dout").innerHTML=d.url?'<a href="'+d.url+'" target="_blank" style="color:#00ff88">Download: '+d.filename+'</a>':d.error;}catch(e){document.getElementById("dout").textContent="Error: "+e.message;}}</script>
</div>'''
    mh = mh.replace("</body>", panel + "</body>")
    open("/home/k/vnt-web/media.html","w").write(mh)
    print("2D drawing panel added to media studio")

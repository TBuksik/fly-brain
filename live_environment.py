"""Local browser interface to a live environment session."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from environment_session import EnvironmentSession


HTML = """<!doctype html>
<html lang="pl">
<meta charset="utf-8">
<title>Fly Brain — podgląd na żywo</title>
<style>
body{font:18px system-ui;background:#111827;color:#e5e7eb;
max-width:900px;margin:40px auto;padding:20px}
canvas{width:100%;background:#1f2937;border-radius:16px}
button{font:inherit;padding:10px 18px;margin:4px;cursor:pointer}
small{display:block;margin-top:20px;color:#9ca3af}
</style>
<h1>Fly Brain: podgląd na żywo</h1>
<canvas id="view" width="900" height="260"></canvas>
<p id="status">Ładowanie…</p>
<button id="play">Uruchom</button>
<button id="step">Jeden krok</button>
<button id="reset">Od początku</button>
<small>Umowna pozycja: 0.1 jednostki na impuls DNg103.
Model wykonuje 10 ms symulacji na krok.</small>
<script>
const canvas=document.querySelector("#view");
const ctx=canvas.getContext("2d");
const status=document.querySelector("#status");
const playButton=document.querySelector("#play");
const stepButton=document.querySelector("#step");
const resetButton=document.querySelector("#reset");
let running=false, busy=false, loopActive=false;

function draw(s){
  const low=Math.min(0,s.position)-0.2;
  const high=Math.max(1,s.position)+0.3;
  const x=p=>50+(p-low)/(high-low)*800;
  ctx.clearRect(0,0,900,260);
  ctx.fillStyle="#14532d";
  ctx.fillRect(x(0),70,x(1)-x(0),120);
  ctx.fillStyle="#bbf7d0";ctx.font="18px system-ui";
  ctx.fillText("Obszar cukru",x(0)+12,95);
  ctx.strokeStyle="#94a3b8";
  ctx.beginPath();ctx.moveTo(50,165);ctx.lineTo(850,165);ctx.stroke();
  const px=x(s.position);
  ctx.fillStyle="#cbd5e1";
  for(const offset of [-9,9]){
    ctx.beginPath();ctx.ellipse(px-3,130+offset,14,7,0,0,Math.PI*2);ctx.fill();
  }
  ctx.fillStyle="#fbbf24";
  ctx.beginPath();ctx.ellipse(px,130,16,6,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle="#111827";
  ctx.beginPath();ctx.arc(px+13,130,5,0,Math.PI*2);ctx.fill();
  status.textContent=`Czas: ${s.time.toFixed(0)} ms | Pozycja: ${s.position.toFixed(2)}
    | Bodziec na następny krok: ${s.rate} Hz | Łącznie impulsów: ${s.spikes}`;
}

function controls(){
  playButton.textContent=running?"Pauza":"Uruchom";
  stepButton.disabled=busy||running||loopActive;
  resetButton.disabled=busy||running||loopActive;
}

async function request(path,method="POST"){
  busy=true;controls();
  try{
    const response=await fetch(path,{method});
    if(!response.ok) throw new Error(await response.text());
    draw(await response.json());
    return true;
  }catch(error){
    running=false;
    status.textContent="Błąd: "+error.message;
    return false;
  }finally{
    busy=false;controls();
  }
}

async function loop(){
  if(loopActive) return;
  loopActive=true;
  try{
    while(running){
      if(!await request("/step")) break;
      await new Promise(resolve=>setTimeout(resolve,50));
    }
  }finally{
    loopActive=false;
    controls();
  }
}

playButton.onclick=()=>{
  running=!running;controls();
  if(running) loop();
};
stepButton.onclick=()=>request("/step");
resetButton.onclick=()=>request("/reset");
playButton.disabled=true;
request("/state","GET").then(()=>{playButton.disabled=false;});
</script>
</html>"""


def main():
    print("Ładowanie mózgu...", flush=True)
    session = EnvironmentSession(seed=42)

    def state():
        return {
            "time": session.brain.time_ms,
            "position": session.movement.position,
            "rate": session.environment.stimulus(session.movement.position),
            "spikes": session.movement.total_spikes,
        }

    class Handler(BaseHTTPRequestHandler):
        def send(self, content, content_type, status=200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            if self.path == "/":
                self.send(HTML.encode(), "text/html; charset=utf-8")
            elif self.path == "/state":
                self.send(json.dumps(state()).encode(), "application/json")
            else:
                self.send(b"Not found", "text/plain", 404)

        def do_POST(self):
            try:
                if self.path == "/step":
                    session.step()
                elif self.path == "/reset":
                    session.reset()
                else:
                    self.send(b"Not found", "text/plain", 404)
                    return
                self.send(json.dumps(state()).encode(), "application/json")
            except Exception as error:
                self.send(str(error).encode(), "text/plain; charset=utf-8", 500)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("Otwórz: http://localhost:8000", flush=True)
    print("Zatrzymanie serwera: Ctrl+C", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

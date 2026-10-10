"""Create a browser replay from an environment trajectory CSV."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", nargs="?")
    args = parser.parse_args()

    directory = Path(__file__).resolve().parent / "data/results/environment"
    if args.csv_path:
        source = Path(args.csv_path)
    else:
        files = list(directory.glob("*.csv"))
        if not files:
            raise SystemExit("Brak CSV. Uruchom najpierw run_environment.py.")
        source = max(files, key=lambda p: p.stat().st_mtime)

    with source.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise SystemExit("CSV nie zawiera kroków.")

    data = [{
        "start": float(row["start_ms"]),
        "end": float(row["end_ms"]),
        "before": float(row["position_before"]),
        "position": float(row["position"]),
        "rate": float(row["sugar_hz"]),
        "left": int(row["dng103_left_spikes"]),
        "right": int(row["dng103_right_spikes"]),
        "spikes": (
            int(row["dng103_left_spikes"])
            + int(row["dng103_right_spikes"])
        ),
    } for row in rows]

    payload = {
        "rows": data,
        "regionStart": float(rows[0]["region_start"]),
        "regionEnd": float(rows[0]["region_end"]),
    }

    html = """<!doctype html>
<html lang="pl">
<meta charset="utf-8">
<title>Fly Brain — odtwarzanie środowiska</title>
<style>
body{font:18px system-ui;background:#111827;color:#e5e7eb;
max-width:900px;margin:40px auto;padding:20px}
canvas{width:100%;background:#1f2937;border-radius:16px}
button{font:inherit;padding:10px 20px;cursor:pointer}
small{display:block;color:#9ca3af;margin:16px 0}
</style>
<h1>Fly Brain: zapisany przebieg</h1>
<p>Zielony obszar oznacza cukier. Symbol muchy pokazuje umowną pozycję.</p>
<canvas id="view" width="900" height="260"></canvas>
<p id="status"></p>
<canvas id="spike-chart" width="900" height="240"></canvas>
<p style="color:#9ca3af;font-size:14px">
Ostatnie 100 zakończonych kroków do wybranego czasu.
Zielone tło oznacza bodziec większy od 0 Hz w danym kroku.
</p>
<button id="replay">Odtwórz ponownie</button>
<button id="pause">Pauza</button>
<p>
<label for="timeline">Czas symulacji:</label>
<input id="timeline" type="range" min="0" value="0" step="0.1"
       style="width:100%">
</p>
<small>Odtwarzanie 20 razy wolniejsze od czasu symulacji.
Ruch wynika z zapisanych impulsów DNg103.</small>
<script>
const data = PAYLOAD;
const canvas = document.querySelector("#view");
const ctx = canvas.getContext("2d");
const status = document.querySelector("#status");
const rows = data.rows;
const low = Math.min(data.regionStart, ...rows.map(r=>r.before)) - 0.2;
const high = Math.max(data.regionEnd, ...rows.map(r=>r.position)) + 0.3;
const x = p => 50 + (p-low)/(high-low)*800;


const chart = document.querySelector("#spike-chart");
const chartCtx = chart.getContext("2d");

function drawSpikes(time){
  const visible = rows.filter(r => r.end <= time).slice(-100);
  const c = chartCtx;
  c.clearRect(0,0,900,240);
  c.textAlign="left";
  c.font="15px system-ui";
  c.fillStyle="#e5e7eb";
  c.fillText("Impulsy w kroku 10 ms",55,25);
  c.fillStyle="#38bdf8";
  c.fillText("Lewy DNg103",400,25);
  c.fillStyle="#fb923c";
  c.fillText("Prawy DNg103",580,25);

  if(!visible.length){
    c.fillStyle="#9ca3af";
    c.fillText("Brak zakończonych kroków w wybranym czasie.",55,110);
    return;
  }

  const maximum=Math.max(1,...visible.map(r=>Math.max(r.left,r.right)));
  const top=45, bottom=195, width=800;
  const y=n=>bottom-n/maximum*(bottom-top);
  const slot=width/visible.length;

  visible.forEach((row,i)=>{
    if(row.rate>0){
      c.fillStyle="#14532d";
      c.fillRect(55+i*slot,top,slot,bottom-top);
    }
  });

  c.textAlign="right";
  for(const value of [...new Set([0,Math.ceil(maximum/2),maximum])]){
    c.strokeStyle="#374151";
    c.beginPath();
    c.moveTo(55,y(value));c.lineTo(855,y(value));c.stroke();
    c.fillStyle="#9ca3af";
    c.fillText(String(value),45,y(value)+5);
  }
  c.textAlign="left";

  visible.forEach((row,i)=>{
    const left=55+i*slot;
    for(const [count,color,offset] of [
      [row.left,"#38bdf8",0.08],
      [row.right,"#fb923c",0.52],
    ]){
      c.fillStyle=color;
      c.fillRect(left+slot*offset,y(count),slot*0.38,bottom-y(count));
    }
  });

  c.fillStyle="#9ca3af";
  c.fillText(`${visible[0].start.toFixed(0)} ms`,55,222);
  c.textAlign="right";
  c.fillText(`${visible[visible.length-1].end.toFixed(0)} ms`,855,222);
  c.textAlign="left";
}

function draw(row, time, position) {
  drawSpikes(time);
  ctx.clearRect(0,0,900,260);
  ctx.fillStyle="#14532d";
  ctx.fillRect(x(data.regionStart),70,
    x(data.regionEnd)-x(data.regionStart),120);
  ctx.fillStyle="#bbf7d0";
  ctx.font="18px system-ui";
  ctx.fillText("Obszar cukru",x(data.regionStart)+12,95);
  ctx.strokeStyle="#94a3b8";
  ctx.beginPath();ctx.moveTo(50,165);ctx.lineTo(850,165);ctx.stroke();

  const px=x(position);
  ctx.fillStyle="#cbd5e1";
  for(const offset of [-9,9]){
    ctx.beginPath();ctx.ellipse(px-3,130+offset,14,7,0,0,Math.PI*2);ctx.fill();
  }
  ctx.fillStyle="#fbbf24";
  ctx.beginPath();ctx.ellipse(px,130,16,6,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle="#111827";
  ctx.beginPath();ctx.arc(px+13,130,5,0,Math.PI*2);ctx.fill();

  status.textContent=`Czas: ${time.toFixed(0)} ms | Pozycja: ${position.toFixed(2)}
    | Bodziec w kroku: ${row.rate} Hz | Impulsy w kroku: ${row.spikes}`;
}

const timeline = document.querySelector("#timeline");
const pauseButton = document.querySelector("#pause");
const firstTime = rows[0].start;
const lastTime = rows[rows.length-1].end;
timeline.min = firstTime;
timeline.max = lastTime;

let frame;
let playing = false;
let currentTime = firstTime;
let previousWallTime;

function render(){
  const row = rows.find(r => currentTime < r.end) || rows[rows.length-1];
  // Zachowujemy skokową aktualizację pozycji z symulacji.
  const position = currentTime >= row.end ? row.position : row.before;
  draw(row, currentTime, position);
  timeline.value = currentTime;
}

function pause(){
  playing = false;
  cancelAnimationFrame(frame);
  pauseButton.textContent = "Wznów";
}

function tick(now){
  if(!playing) return;
  currentTime = Math.min(
    currentTime + (now - previousWallTime) / 20,
    lastTime
  );
  previousWallTime = now;
  render();
  if(currentTime >= lastTime){
    pause();
  } else {
    frame = requestAnimationFrame(tick);
  }
}

function play(){
  if(playing) return;
  if(currentTime >= lastTime) currentTime = firstTime;
  playing = true;
  previousWallTime = performance.now();
  pauseButton.textContent = "Pauza";
  render();
  frame = requestAnimationFrame(tick);
}

function replay(){
  pause();
  currentTime = firstTime;
  play();
}

pauseButton.onclick = () => playing ? pause() : play();
timeline.oninput = () => {
  pause();
  currentTime = Number(timeline.value);
  render();
};
document.querySelector("#replay").onclick = replay;
replay();
</script>
</html>"""

    output = source.with_suffix(".html")
    output.write_text(
        html.replace("PAYLOAD", json.dumps(payload, allow_nan=False)),
        encoding="utf-8",
    )
    print("CSV:", source)
    print("Podgląd:", output)


if __name__ == "__main__":
    main()

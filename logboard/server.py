from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader
import asyncio, json
from pathlib import Path

app = FastAPI()
LOG_PATH = Path("logs/app.log")

env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
template = env.get_template("index.html")

@app.get("/", response_class=HTMLResponse)
async def show_page():
    return template.render()

async def stream_logs():
    last_size = 0
    while True:
        if LOG_PATH.exists():
            size = LOG_PATH.stat().st_size
            if size < last_size:
                last_size = 0
            if size > last_size:
                with LOG_PATH.open() as f:
                    f.seek(last_size)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            yield f"data: {json.dumps(obj)}\n\n"
                        except json.JSONDecodeError:
                            continue
                    last_size = f.tell()
        await asyncio.sleep(1)

@app.get("/stream")
async def sse_endpoint():
    return StreamingResponse(stream_logs(), media_type="text/event-stream")

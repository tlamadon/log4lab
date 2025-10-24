from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from jinja2 import Environment, FileSystemLoader
import asyncio, json
from pathlib import Path
import mimetypes

# Global variable to store the log path
_LOG_PATH = Path("logs/app.log")

env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
template = env.get_template("index.html")

def set_log_path(log_path: Path):
    """Set the log path for the server."""
    global _LOG_PATH
    _LOG_PATH = log_path

def get_log_path() -> Path:
    """Get the current log path."""
    return _LOG_PATH

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def show_page():
    return template.render()

@app.get("/runs", response_class=HTMLResponse)
async def show_runs_page():
    """Show the run IDs index page."""
    runs_template = env.get_template("runs.html")
    return runs_template.render()

@app.get("/api/runs")
async def get_runs():
    """Get run_names with their run_ids from the log file."""
    log_path = get_log_path()
    runs = {}  # {run_name: {run_ids: [{run_id, count}], total: X}}

    if log_path.exists():
        with log_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    run_name = obj.get('run_name')
                    run_id = obj.get('run_id')

                    if run_name:
                        run_name = str(run_name)
                        if run_name not in runs:
                            runs[run_name] = {'run_ids': {}, 'total': 0}

                        runs[run_name]['total'] += 1

                        if run_id:
                            run_id = str(run_id)
                            if run_id not in runs[run_name]['run_ids']:
                                runs[run_name]['run_ids'][run_id] = 0
                            runs[run_name]['run_ids'][run_id] += 1

                except json.JSONDecodeError:
                    continue

    # Convert to frontend-friendly format
    result = {}
    for run_name, data in runs.items():
        result[run_name] = {
            'total': data['total'],
            'run_ids': [
                {'run_id': rid, 'count': count}
                for rid, count in sorted(data['run_ids'].items())
            ]
        }

    return {"runs": result}

async def stream_logs():
    last_size = 0
    while True:
        log_path = get_log_path()
        if log_path.exists():
            size = log_path.stat().st_size
            if size < last_size:
                last_size = 0
            if size > last_size:
                with log_path.open() as f:
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

@app.get("/cache/{file_path:path}")
async def serve_cache_file(file_path: str):
    """Serve cache files relative to the log file directory."""
    log_dir = get_log_path().parent
    requested_file = log_dir / file_path

    # Security: ensure the file is within the log directory or subdirectories
    try:
        requested_file = requested_file.resolve()
        log_dir = log_dir.resolve()
        if not str(requested_file).startswith(str(log_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not requested_file.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not requested_file.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Determine the media type
    mime_type, _ = mimetypes.guess_type(str(requested_file))
    if mime_type is None:
        mime_type = "application/octet-stream"

    return FileResponse(requested_file, media_type=mime_type)

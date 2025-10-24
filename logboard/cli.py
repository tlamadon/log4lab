import typer
import uvicorn
from pathlib import Path
from . import server

app = typer.Typer(help="LogBoard — a lightweight structured log dashboard")


@app.command()
def serve(
    logfile: Path = typer.Argument(
        "logs/app.log",
        exists=False,
        help="Path to the JSONL log file to stream (default: logs/app.log)"
    ),
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the LogBoard web server."""
    server.set_log_path(logfile)
    uvicorn.run("logboard.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()


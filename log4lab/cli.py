import typer
import uvicorn
from pathlib import Path
from typing import Optional
from . import server
from .tail import LogTailer

app = typer.Typer(help="Log4Lab — a lightweight structured log dashboard")


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
    """Start the Log4Lab web server."""
    server.set_log_path(logfile)
    uvicorn.run("log4lab.server:app", host=host, port=port, reload=reload)


@app.command()
def tail(
    logfile: Path = typer.Argument(
        "logs/app.log",
        help="Path to the JSONL log file to tail"
    ),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter by log level (e.g., INFO, ERROR)"),
    section: Optional[str] = typer.Option(None, "--section", "-s", help="Filter by section name"),
    run_name: Optional[str] = typer.Option(None, "--run-name", "-r", help="Filter by run name"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Filter by run ID"),
    group: Optional[str] = typer.Option(None, "--group", "-g", help="Filter by group name"),
    time_range: Optional[int] = typer.Option(None, "--time-range", "-t", help="Only show logs from last N seconds"),
    follow: bool = typer.Option(True, "--follow/--no-follow", "-f", help="Follow log file for new entries"),
    show_images: bool = typer.Option(True, "--images/--no-images", help="Try to show images inline in terminal"),
    open_images: bool = typer.Option(False, "--open-images", help="Open images in system default viewer (Preview, etc.)"),
):
    """Tail logs to the terminal with rich formatting and filters."""
    tailer = LogTailer(
        log_path=logfile,
        level=level,
        section=section,
        run_name=run_name,
        run_id=run_id,
        group=group,
        time_range=time_range,
        follow=follow,
        show_images=show_images,
        open_images=open_images,
    )
    try:
        tailer.tail()
    except KeyboardInterrupt:
        pass  # Clean exit on Ctrl+C


if __name__ == "__main__":
    app()


"""Terminal-based log tailing with live streaming and image support."""
import json
import time
import subprocess
import platform
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich import box

try:
    from term_image.image import from_file
    IMAGES_SUPPORTED = True
except (ImportError, Exception):
    # term-image may not be available or may have dependency issues
    IMAGES_SUPPORTED = False


class LogTailer:
    """Tail JSONL log files with rich terminal output."""

    def __init__(
        self,
        log_path: Path,
        level: Optional[str] = None,
        section: Optional[str] = None,
        run_name: Optional[str] = None,
        run_id: Optional[str] = None,
        group: Optional[str] = None,
        time_range: Optional[int] = None,
        follow: bool = True,
        show_images: bool = True,
        open_images: bool = False,
    ):
        self.log_path = log_path
        self.level = level.upper() if level else None
        self.section = section
        self.run_name = run_name
        self.run_id = run_id
        self.group = group
        self.time_range = time_range  # seconds
        self.follow = follow
        self.show_images = show_images and IMAGES_SUPPORTED
        self.open_images = open_images
        self.console = Console()

    def matches_filters(self, entry: dict) -> bool:
        """Check if log entry matches all filters."""
        # Level filter
        if self.level and entry.get("level", "").upper() != self.level:
            return False

        # Section filter
        if self.section and self.section.lower() not in entry.get("section", "").lower():
            return False

        # Run name filter
        if self.run_name and self.run_name.lower() not in entry.get("run_name", "").lower():
            return False

        # Run ID filter
        if self.run_id and self.run_id.lower() not in entry.get("run_id", "").lower():
            return False

        # Group filter
        if self.group and self.group.lower() not in entry.get("group", "").lower():
            return False

        # Time range filter
        if self.time_range and "time" in entry:
            try:
                log_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if (now - log_time).total_seconds() > self.time_range:
                    return False
            except (ValueError, AttributeError):
                pass

        return True

    def format_level(self, level: str) -> Text:
        """Format log level with colors."""
        level = level.upper()
        colors = {
            "ERROR": "red bold",
            "WARN": "yellow bold",
            "WARNING": "yellow bold",
            "INFO": "blue bold",
            "DEBUG": "cyan",
            "TRACE": "dim",
        }
        color = colors.get(level, "white")
        return Text(level.ljust(7), style=color)

    def format_timestamp(self, timestamp: str) -> Text:
        """Format timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return Text(dt.strftime("%H:%M:%S"), style="dim")
        except (ValueError, AttributeError):
            return Text(timestamp[:8] if len(timestamp) > 8 else timestamp, style="dim")

    def format_entry(self, entry: dict) -> Panel:
        """Format a log entry as a rich panel."""
        # Header with timestamp, level, and metadata
        header_parts = []

        if "time" in entry:
            header_parts.append(self.format_timestamp(entry["time"]))

        if "level" in entry:
            header_parts.append(self.format_level(entry["level"]))

        if "section" in entry:
            header_parts.append(Text(f"[{entry['section']}]", style="magenta"))

        if "run_name" in entry:
            header_parts.append(Text(f"run:{entry['run_name']}", style="green"))

        if "run_id" in entry:
            header_parts.append(Text(f"id:{entry['run_id']}", style="green dim"))

        if "group" in entry:
            header_parts.append(Text(f"group:{entry['group']}", style="yellow"))

        header = Text(" ").join(header_parts)

        # Message (main content)
        message = entry.get("message") or entry.get("msg") or entry.get("event", "")
        message_text = Text(message, style="white")

        # Additional fields (exclude known fields)
        known_fields = {"time", "level", "section", "message", "msg", "event", "run_name", "run_id", "group", "cache_path"}
        extra_fields = {k: v for k, v in entry.items() if k not in known_fields}

        content_parts = [message_text]

        if extra_fields:
            content_parts.append(Text("\n"))
            extra_text = Text(json.dumps(extra_fields, indent=2), style="dim")
            content_parts.append(extra_text)

        content = Text("").join(content_parts)

        # Create panel
        border_style = {
            "ERROR": "red",
            "WARN": "yellow",
            "WARNING": "yellow",
            "INFO": "blue",
            "DEBUG": "cyan",
        }.get(entry.get("level", "").upper(), "white")

        panel = Panel(
            content,
            title=header,
            title_align="left",
            border_style=border_style,
            box=box.ROUNDED,
        )

        return panel

    def open_image_externally(self, image_path: Path):
        """Open image in system default viewer."""
        try:
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.run(['open', str(image_path)], check=True)
            elif system == 'Linux':
                subprocess.run(['xdg-open', str(image_path)], check=True)
            elif system == 'Windows':
                subprocess.run(['start', str(image_path)], shell=True, check=True)
            self.console.print(f"[dim green]✓ Opened {image_path.name} in system viewer[/dim green]")
        except Exception as e:
            self.console.print(f"[dim yellow]Could not open image: {e}[/dim yellow]")

    def show_image(self, image_path: Path):
        """Display image inline in terminal if supported."""
        if not image_path.exists():
            self.console.print(f"[dim red]📷 Image not found: {image_path}[/dim red]")
            return

        # Check if file is an image
        if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
            self.console.print(f"[dim]📄 File: {image_path}[/dim]")
            return

        # Option 1: Open in external viewer (most reliable)
        if self.open_images:
            self.open_image_externally(image_path)
            return

        # Option 2: Show path with helpful message (default behavior)
        # Inline rendering is disabled by default due to unreliability
        self.console.print(f"[dim cyan]📷 Image: {image_path}[/dim cyan]")
        if self.show_images:
            self.console.print(f"[dim]   💡 Tip: Use --open-images to view in Preview/image viewer[/dim]")

    def tail(self):
        """Tail the log file and display entries."""
        if not self.log_path.exists():
            self.console.print(f"[red]Error: Log file not found: {self.log_path}[/red]")
            return

        # Print header
        self.console.print(Panel(
            f"[bold]Tailing log file:[/bold] {self.log_path}\n"
            f"[dim]Press Ctrl+C to stop[/dim]",
            border_style="blue",
        ))

        # Show active filters
        if any([self.level, self.section, self.run_name, self.run_id, self.group, self.time_range]):
            filters = []
            if self.level:
                filters.append(f"level={self.level}")
            if self.section:
                filters.append(f"section={self.section}")
            if self.run_name:
                filters.append(f"run_name={self.run_name}")
            if self.run_id:
                filters.append(f"run_id={self.run_id}")
            if self.group:
                filters.append(f"group={self.group}")
            if self.time_range:
                filters.append(f"time_range={self.time_range}s")
            self.console.print(f"[yellow]Active filters: {', '.join(filters)}[/yellow]\n")

        with open(self.log_path, 'r') as f:
            # Read existing lines first
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    if self.matches_filters(entry):
                        self.console.print(self.format_entry(entry))

                        # Show image if cache_path exists
                        if "cache_path" in entry:
                            cache_path = Path(entry["cache_path"])
                            if not cache_path.is_absolute():
                                cache_path = self.log_path.parent / cache_path
                            self.show_image(cache_path)

                        self.console.print()  # Empty line between entries
                except json.JSONDecodeError:
                    continue

            # Follow mode: watch for new lines
            if self.follow:
                while True:
                    line = f.readline()
                    if line:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                if self.matches_filters(entry):
                                    self.console.print(self.format_entry(entry))

                                    # Show image if cache_path exists
                                    if "cache_path" in entry:
                                        cache_path = Path(entry["cache_path"])
                                        if not cache_path.is_absolute():
                                            cache_path = self.log_path.parent / cache_path
                                        self.show_image(cache_path)

                                    self.console.print()  # Empty line between entries
                            except json.JSONDecodeError:
                                continue
                    else:
                        time.sleep(0.1)  # Short sleep to avoid busy waiting

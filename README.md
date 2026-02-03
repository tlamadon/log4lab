# Log4Lab

A lightweight structured log viewer with live streaming, filtering, and rich content rendering.

Log4Lab is a web-based dashboard for viewing and analyzing structured JSON logs in real-time. It provides a clean interface for monitoring application logs with live updates, making it easy to track experiments and debug issues.

## Installation

### Using pipx (Recommended)

Install log4lab as an isolated application:

```bash
pipx install log4lab
```

### Using pip

```bash
pip install log4lab
```

### From source

```bash
git clone https://github.com/tlamadon/log4lab.git
cd log4lab
pip install -e .
```

## Quick Start

1. **Start the web interface:**
   ```bash
   log4lab serve logs/app.log
   ```
   Then open http://localhost:8000

2. **View logs in terminal:**
   ```bash
   log4lab tail logs/app.log
   ```

3. **Export to HTML:**
   ```bash
   log4lab export logs/app.log -o report.html
   ```

## Log Format

Log4Lab expects JSONL format (one JSON object per line):

```json
{"time": "2025-02-03T10:30:00Z", "level": "INFO", "section": "train", "message": "Training started"}
{"time": "2025-02-03T10:30:05Z", "level": "WARN", "section": "data", "message": "Missing data point"}
{"time": "2025-02-03T10:30:10Z", "level": "ERROR", "section": "model", "message": "Model failed to converge"}
```

### With Rich Content

Log4Lab can display various file types when you include a `cache_path` field:

```json
{
  "time": "2025-02-03T10:30:00Z",
  "level": "INFO",
  "section": "train",
  "message": "Training complete",
  "cache_path": "artifacts/results.png",
  "run_name": "experiment_1",
  "accuracy": 0.95
}
```

**Supported content types:**
- **Images**: PNG, JPG, SVG, etc. (displayed inline)
- **Code files**: Python, JavaScript, JSON, YAML, etc. (syntax highlighted, collapsible)
- **Markdown**: .md files (rendered as HTML, collapsible)
- **PDFs**: Embedded viewer
- **Other files**: Download links

### Core Fields

- `time`: Timestamp in ISO 8601 format
- `level`: Log level (INFO, WARN, ERROR, DEBUG)
- `section`: Component or module name
- `message` or `msg`: Main log message
- `cache_path`: Path to artifact file
- `run_name`: Name of the run collection
- `run_id`: Unique run identifier

Any additional fields are shown in the expandable JSON view.

## Commands

### Serve (Web Interface)

```bash
log4lab serve [LOGFILE]

# Options:
--host 0.0.0.0        # Bind to all interfaces (default: 127.0.0.1)
--port 3000           # Custom port (default: 8000)
--reload              # Auto-reload for development
```

### Tail (Terminal)

```bash
log4lab tail [LOGFILE]

# Options:
--level ERROR         # Filter by log level
--open-images         # Open images automatically
```

### Export

```bash
log4lab export [LOGFILE] -o output.html

# Options:
-o, --output FILE     # Output file path
-t, --title TEXT      # Custom page title
--no-embed-images     # Don't embed images (smaller file)
```

## Filtering

The web interface supports:
- **Level filtering**: Dropdown with all levels found in logs
- **Text filters**: Section, run name, run ID (partial matching)
- **Time range**: Last 1m, 5m, 30m, 1h, 6h, 24h
- **URL filters**: Bookmark and share filtered views

```
# Filter by error logs from last hour
http://localhost:8000/?level=error&time=3600

# View specific run
http://localhost:8000/?run_name=experiment_1
```

## Use Cases

**Machine Learning**: Track training runs with metrics and plots
```json
{"run_name": "resnet_training", "epoch": 10, "loss": 0.23, "cache_path": "plots/loss.png"}
```

**Debugging**: Monitor distributed systems across components
```json
{"section": "api", "level": "ERROR", "message": "Connection timeout", "duration_ms": 5000}
```

**Research**: Document experiments with artifacts
```json
{"run_name": "param_sweep", "message": "Testing lr=0.001", "cache_path": "results.pdf"}
```

## License

MIT
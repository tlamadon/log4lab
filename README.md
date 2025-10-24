# LogBoard

A powerful, lightweight structured log viewer with live streaming, advanced filtering, and run tracking capabilities.

LogBoard is a web-based dashboard for viewing and analyzing structured JSON logs in real-time. It provides a clean, modern interface for monitoring application logs with live updates, making it easy to track experiments, debug issues, and understand what's happening in your applications.

## Features

### Core Functionality
- **Live Log Streaming**: Automatically streams new log entries as they're written to the log file using Server-Sent Events (SSE)
- **Structured Log Support**: Parses and displays JSONL (JSON Lines) formatted logs
- **Relative Time Display**: Shows "how long ago" each entry was created with automatic updates
- **Dark Mode**: Built-in dark mode support with theme persistence in browser local storage

### Advanced Filtering
- **Level Filter**: Dynamically populated dropdown based on actual log levels in your file (case-insensitive)
- **Section Filter**: Filter by component or section name
- **Group Filter**: Filter by experiment or job group
- **Run Name Filter**: Filter by run name to see all runs in a collection
- **Run ID Filter**: Focus on a specific run instance
- **Time Range Filter**: View logs from the last 1 minute, 5 minutes, 1 hour, 6 hours, or 24 hours
- **URL-based Filters**: All filters can be passed as URL query parameters for bookmarking and sharing

### Run Management
- **Runs Index Page**: Hierarchical view showing all run names with their associated run IDs
- **Run Links**: Each log entry includes a clickable link to filter by its run name or run ID
- **Run Statistics**: See total log counts per run name and individual run ID

### Display & Navigation
- **Pagination**: Configurable page size (20, 50, 100, or 200 entries per page)
- **Sort Toggle**: Switch between newest-first and oldest-first ordering (perfect for reviewing run chronology)
- **Collapsible JSON**: Full JSON view available for each entry, collapsed by default
- **Smart Message Display**: Renders the `message` field as the main content in fixed-width font
- **Artifact Rendering**: Automatically displays images, PDFs, and files referenced in the `cache_path` field

### User Interface
- **Modern Design**: Built with Tailwind CSS for a clean, responsive interface
- **Smooth Navigation**: Scroll to top on page changes, smooth transitions
- **Keyboard-Friendly**: All filters and controls are easily accessible

## Installation

```bash
pip install logboard
```

Or install from source:

```bash
git clone https://github.com/yourusername/logboard.git
cd logboard
pip install -e .
```

## Usage

Start the LogBoard server:

```bash
logboard [LOGFILE]
```

### Options

- `LOGFILE`: Path to the JSONL log file to stream (default: `logs/app.log`)
- `--host`: Host to bind to (default: `127.0.0.1`)
- `--port`: Port to listen on (default: `8000`)
- `--reload`: Enable auto-reload for development

### Examples

```bash
# Use default log file (logs/app.log)
logboard

# Specify a custom log file
logboard /path/to/your/app.log

# Run on a different port
logboard myapp.log --port 3000

# Bind to all interfaces
logboard myapp.log --host 0.0.0.0

# Development mode with auto-reload
logboard --reload
```

Then open your browser to `http://localhost:8000` to view the dashboard.

### Using Filters via URL

Share specific filtered views by passing query parameters:

```bash
# View only ERROR logs
http://localhost:8000/?level=error

# View a specific run
http://localhost:8000/?run_id=abc123

# View all runs in a collection
http://localhost:8000/?run_name=model_training

# Combine multiple filters
http://localhost:8000/?level=error&run_name=experiment1&time=3600
```

## Log Format

LogBoard expects logs in JSONL format (one JSON object per line). Each log entry should be a JSON object.

### Basic Example

```json
{"time": "2025-10-24T10:30:00Z", "level": "INFO", "section": "train", "message": "Training started"}
{"time": "2025-10-24T10:30:05Z", "level": "WARN", "section": "data", "message": "Missing data point"}
{"time": "2025-10-24T10:30:10Z", "level": "ERROR", "section": "model", "message": "Model failed to converge"}
```

### Advanced Example with Runs and Artifacts

```json
{
  "time": "2025-10-24T10:30:00Z",
  "level": "INFO",
  "section": "train",
  "message": "Training epoch 1 complete",
  "run_name": "model_training",
  "run_id": "run_001",
  "group": "experiment_1",
  "cache_path": "artifacts/training_plot.png",
  "accuracy": 0.92,
  "loss": 0.15
}
```

### Supported Fields

#### Core Fields
- `time`: Timestamp in ISO 8601 format (automatically handles UTC if no timezone specified)
- `level`: Log level (INFO, WARN, ERROR, DEBUG, etc.) - case-insensitive
- `section`: Component or section of your application
- `message` or `msg`: The main log message (displayed prominently in fixed-width font)

#### Run Tracking Fields
- `run_name`: Name of the run collection (e.g., "hyperparameter_search")
- `run_id`: Unique identifier for a specific run instance
- `group`: Group or experiment name for organizing related runs

#### Artifact Fields
- `cache_path`: Path to an artifact file (images, PDFs, etc.)
  - Images (PNG, JPG, SVG, etc.) are displayed inline
  - PDFs are embedded with a viewer
  - Other files show as download links

#### Additional Fields
Any additional fields (metrics, parameters, etc.) are displayed in the expandable JSON view.

## Features in Detail

### Live Streaming

LogBoard monitors the log file for changes and automatically streams new entries to the browser using Server-Sent Events (SSE). New entries appear at the top with smooth animations, and the "time ago" display updates every 5 seconds.

### Time Display

Each log entry shows:
- Relative time (e.g., "just now", "5m ago", "2h ago", "3d ago")
- Absolute timestamp for reference
- Automatic handling of UTC timestamps
- Smart future timestamp detection (shows "in 2h" for logs from the future)

### Filtering System

**Dynamic Level Filter**: Automatically discovers all log levels in your file and populates the dropdown. Supports any level names (INFO, Error, debug, WARN, etc.) with case-insensitive matching.

**Text Filters**: Section, Group, Run Name, and Run ID filters support partial matching and are case-insensitive.

**Time Range Filter**: Show only recent logs:
- Last 1 minute
- Last 5 minutes
- Last 10 minutes
- Last 30 minutes
- Last 1 hour
- Last 6 hours
- Last 24 hours

**Filter Persistence**: All filters are reflected in the URL, so you can bookmark specific views or share links with teammates.

### Run Management

The **Runs Index** (`/runs`) provides a bird's-eye view of all your runs:
- Lists all unique run names
- Shows total log count per run name
- Displays all associated run IDs with individual counts
- Click any run name to see all logs for that collection
- Click any run ID to see logs for that specific instance

Each log entry includes a **run info link** that takes you directly to a filtered view of that run.

### Sorting

Toggle between two sort orders:
- **Newest First** (default): Latest logs appear at the top - ideal for monitoring
- **Oldest First**: Chronological order from the beginning - perfect for understanding run progression

### Pagination

Control how many logs appear per page (20, 50, 100, or 200) and navigate through pages with Previous/Next buttons. The display shows your current position (e.g., "Showing 1-50 of 153 logs").

### Artifact Display

If your logs include a `cache_path` field pointing to artifacts:

**Images**: Displayed inline with full size
```json
{"cache_path": "artifacts/plot.png", "message": "Training loss over time"}
```

**PDFs**: Embedded with a document viewer
```json
{"cache_path": "artifacts/report.pdf", "message": "Experiment results"}
```

**Other Files**: Download link provided
```json
{"cache_path": "artifacts/model.pkl", "message": "Model checkpoint saved"}
```

### Theme Support

Toggle between light and dark modes with the theme button in the top-right corner. Your preference is saved in browser local storage and persists across sessions.

## Use Cases

### Machine Learning Experiments

Track training runs with metrics, visualizations, and hyperparameters:

```json
{"time": "2025-10-24T10:30:00Z", "level": "INFO", "run_name": "resnet_training", "run_id": "exp_001", "message": "Epoch 1/100", "loss": 0.45, "accuracy": 0.78, "cache_path": "plots/loss_curve.png"}
```

View all runs for a training session, compare metrics across runs, and review training progression chronologically.

### Distributed Systems Debugging

Monitor services across multiple components:

```json
{"time": "2025-10-24T10:30:00Z", "level": "ERROR", "section": "api", "group": "prod", "message": "Connection timeout to database", "duration_ms": 5000}
```

Filter by section to isolate component issues, use time range to focus on incident windows, and track error patterns.

### Research Workflows

Document experiments with notes and artifacts:

```json
{"time": "2025-10-24T10:30:00Z", "level": "INFO", "run_name": "parameter_sweep", "run_id": "sweep_042", "message": "Testing learning_rate=0.001", "cache_path": "results/metrics.pdf"}
```

Compare results across parameter sweeps, review experimental progression, and access generated reports directly from logs.

## Development

To run LogBoard in development mode with auto-reload:

```bash
logboard --reload
```

## Requirements

- Python >= 3.8
- FastAPI
- Uvicorn
- Jinja2
- Typer

## License

MIT

## Author

Thibaut Lamadon

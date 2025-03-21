# WebSocket Stress Tester

A progressive WebSocket connection stress testing tool that measures how many simultaneous WebSocket connections your client or server can handle.

## Features

- 🔄 Tests increasing numbers of simultaneous WebSocket connections
- ⏱️ Holds batches of connections open for a configurable duration
- 📊 Reports detailed connection statistics and performance metrics
- 🚦 Automatically detects stability thresholds
- 📈 Measures response times for all connections
- 🖥️ Provides system information for troubleshooting
- ⚙️ YAML configuration for easy customization

## Installation

```bash
# Clone the repository
git clone https://github.com/veryraregaming/WebSocket-Stress-Tester
cd WebSocket-Stress-Tester

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The tool uses a `config.yaml` file for its settings. Example configuration:

```yaml
# Server connection settings
server:
  host: "example.com"
  port: 8080
  protocol: "ws"  # ws or wss
  path: "/"

# Connection test settings
test:
  start_connections: 1
  max_connections: 10
  increment: 1
  batch_duration: 5  # seconds
  connection_delay: 0  # seconds
  stability_threshold: 90.0  # percentage
```

Edit this file to change default settings or use command-line arguments to override them.

## Test Server

For local testing, a simple WebSocket echo server script is included:

```bash
# On Linux/Mac:
chmod +x server.sh
./server.sh

# This will:
# 1. Create a Python virtual environment
# 2. Install required dependencies
# 3. Start a WebSocket echo server on port 7070
```

Once the server is running, you can test against it with:

```bash
python main.py --host localhost --port 7070
```

## Usage

```bash
# Basic usage with settings from config.yaml
python main.py

# Test against a different WebSocket server
python main.py --host other-server.com --port 8080

# Increase the maximum number of connections
python main.py --max 50 --increment 5

# Hold connections open longer (seconds)
python main.py --duration 10

# Add delay between opening connections (seconds)
python main.py --delay 0.1
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--host` | WebSocket server hostname |
| `--port` | WebSocket server port |
| `--protocol` | WebSocket protocol (ws or wss) |
| `--path` | WebSocket endpoint path |
| `--start` | Starting number of connections |
| `--max` | Maximum number of connections to test |
| `--increment` | How many connections to add in each batch |
| `--duration` | How long to keep the entire batch open in seconds |
| `--delay` | Delay in seconds between starting individual connections |

## Output

The tool provides detailed output including:
- Connection success/failure rates
- Response time statistics (average, min, max)
- Network usage statistics
- System information for context
- Connection stability analysis
- Maximum stable connection count

## Requirements

- Python 3.7+
- websockets
- psutil
- PyYAML

## License

MIT 
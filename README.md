# WebSocket Stress Tester

A tool for testing WebSocket server performance and connection limits by progressively increasing the number of simultaneous connections.

## Features

- Test WebSocket server capacity with multiple simultaneous connections
- Gradually increase connections to find stability thresholds
- Cumulative testing mode to keep existing connections open while adding new ones
- Detailed statistics on connection success rates and response times
- Configurable connection parameters through YAML file or command line arguments

## Installation

```bash
# Clone the repository
git clone https://github.com/veryraregaming/WebSocket-Stress-Tester.git
cd WebSocket-Stress-Tester

# Install requirements
pip install -r requirements.txt
```

## Configuration

Edit the `config.yaml` file to set your WebSocket server details and testing parameters:

```yaml
server:
  host: "example.com"
  port: 8080
  protocol: "ws"  # ws or wss
  path: "/"
```

## Usage

Basic usage with default settings from config.yaml:

```bash
python main.py
```

With command line arguments (overrides config file):

```bash
python main.py --host example.com --port 8080 --start 10 --max 100 --increment 5 --duration 10 --cumulative
```

### Parameters

- `--host`: WebSocket server hostname
- `--port`: WebSocket server port
- `--protocol`: Protocol (ws or wss)
- `--path`: WebSocket endpoint path
- `--start`: Starting number of connections
- `--max`: Maximum number of connections to test
- `--increment`: How many connections to add in each batch
- `--duration`: How long to keep the entire batch open in seconds
- `--delay`: Delay in seconds between starting individual connections
- `--cumulative`: Keep previous connections open when adding new ones

## Cumulative Mode

In cumulative mode, each batch keeps existing connections open and adds new ones. This helps test how servers handle increasing connection loads over time.

Example command:
```bash
python main.py --cumulative --start 20 --increment 10 --max 200
```

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
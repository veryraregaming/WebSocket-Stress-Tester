
# WebSocket Stress Tester

A tool for testing WebSocket server performance and connection limits by progressively increasing the number of simultaneous connections.

## Features

- Test WebSocket server capacity with multiple simultaneous connections
- Supports both `ws://` and `wss://` protocols
- Cumulative testing mode to keep existing connections open while adding new ones
- Detailed statistics on connection success rates and response times
- Configurable connection parameters via YAML or command-line
- Optional secure echo server with self-signed TLS certificate

## Installation

```bash
# Clone the repository
git clone https://github.com/veryraregaming/WebSocket-Stress-Tester.git
cd WebSocket-Stress-Tester

# Install requirements
pip install -r requirements.txt

# Copy and edit the config file
cp example_config.yaml config.yaml
```

## Configuration

Edit `config.yaml` to match your WebSocket server:

```yaml
server:
  host: "your-server.com"
  port: 8080
  protocol: "ws"  # Options: "ws" or "wss"
  path: "/"
```

You can override these with CLI flags.

## Usage

Run with the config file:

```bash
python main.py
```

Or override with command-line arguments:

```bash
python main.py --host example.com --port 8080 --protocol wss --start 10 --max 100 --increment 5 --duration 10 --cumulative
```

### Command Line Parameters

- `--host`: WebSocket server hostname
- `--port`: WebSocket server port
- `--protocol`: `ws` or `wss`
- `--path`: WebSocket endpoint path
- `--start`: Starting number of connections
- `--max`: Maximum number of connections
- `--increment`: How many to add per batch
- `--duration`: Batch duration in seconds
- `--delay`: Delay between starting connections (seconds)
- `--cumulative`: Enable cumulative mode (keep previous connections alive)
- `--verbose`: Show detailed per-connection logs

## Cumulative Mode

In cumulative mode, each batch keeps existing connections open and adds more, allowing you to observe server performance under increasing load.

```bash
python main.py --cumulative --start 20 --increment 10 --max 200
```

## Test Servers

### 1. Unencrypted Echo Server (`ws://`)
To run a basic WebSocket echo server on `ws://localhost:7070`:

```bash
chmod +x server.sh
./server.sh
```

This script will:
- Create a virtual environment
- Install dependencies
- Start a plain WebSocket echo server

Test it with:

```bash
python main.py --host localhost --port 7070 --protocol ws
```

---

### 2. Secure Echo Server (`wss://`)
To run a secure WebSocket echo server on `wss://localhost:7070` with self-signed TLS:

```bash
chmod +x wssserver.sh
sudo ./wssserver.sh
```

This script will:
- Set up a virtual environment
- Install dependencies
- Generate a self-signed certificate (cert.pem + key.pem)
- Start a secure WebSocket server using TLS

Test it with:

```bash
python main.py --host localhost --port 7070 --protocol wss
```

📌 _Note: Self-signed certs are fine for local testing, but you'll need valid certs for production use._

---

## Output

You'll receive detailed feedback including:
- Connection success/failure rates
- Response times (avg, min, max)
- Network stats (optional)
- System info (optional)
- Connection stability analysis
- Estimated max stable connection count

## Requirements

- Python 3.7+
- `websockets`
- `psutil`
- `PyYAML`

Install everything with:

```bash
pip install -r requirements.txt
```

## License

MIT

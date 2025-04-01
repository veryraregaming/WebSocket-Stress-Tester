#!/bin/bash

# Secure WebSocket Echo Server Runner with Virtual Environment and Self-Signed TLS

# Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install websockets in the virtual environment
echo "📦 Installing websockets package in virtual environment..."
pip install --quiet websockets

# Generate self-signed certificate if not found
if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
    echo "🔐 Generating self-signed TLS certificate (cert.pem & key.pem)..."
    openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 365 \
        -subj "/CN=localhost"
fi

# Create the secure server.py script if it doesn't exist
if [ ! -f "server.py" ]; then
    echo "📝 Creating server.py file..."
    cat > server.py << 'EOF'
#!/usr/bin/env python3
# Secure WebSocket Echo Server using self-signed certs

import asyncio
import websockets
import ssl
import signal
import sys

HOST = '0.0.0.0'
PORT = 7070
CERT_FILE = 'cert.pem'
KEY_FILE = 'key.pem'

active_connections = set()

async def handle_connection(websocket):
    connection_id = len(active_connections) + 1
    active_connections.add(websocket)
    client_info = websocket.remote_address
    print(f"[+] Client {connection_id} connected from {client_info[0]}:{client_info[1]}")
    print(f"[i] Active connections: {len(active_connections)}")

    try:
        async for message in websocket:
            print(f"[>] Received from client {connection_id}: {message}")
            await websocket.send(message)
            print(f"[<] Echoed to client {connection_id}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"[!] Client {connection_id} disconnected: {e}")
    except Exception as e:
        print(f"[!] Error with client {connection_id}: {e}")
    finally:
        active_connections.remove(websocket)
        print(f"[-] Client {connection_id} removed")
        print(f"[i] Active connections: {len(active_connections)}")

def handle_shutdown(signal_received, frame):
    print("\n[!] Shutdown signal received. Stopping server...")
    sys.exit(0)

async def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    server = await websockets.serve(
        handle_connection,
        HOST,
        PORT,
        ssl=ssl_context
    )

    print(f"[i] Secure WebSocket Echo Server running on wss://{HOST}:{PORT}")
    print(f"[i] Press Ctrl+C to stop the server")

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
EOF
fi

# Make the server script executable
chmod +x server.py

# Start the secure WebSocket server
echo "🚀 Starting Secure WebSocket Echo Server on wss://0.0.0.0:7070"
python server.py

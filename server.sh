#!/bin/bash

# WebSocket Echo Server Runner with Virtual Environment

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install websockets in the virtual environment
echo "Installing websockets package in virtual environment..."
pip install websockets

# Create the server.py file if it doesn't exist
if [ ! -f "server.py" ]; then
    echo "Creating server.py file..."
    cat > server.py << 'EOF'
#!/usr/bin/env python3
# Simple WebSocket Echo Server

import asyncio
import websockets
import signal
import sys

# Server configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 7070

# Track active connections
active_connections = set()

async def handle_connection(websocket):
    # Register connection
    connection_id = len(active_connections) + 1
    active_connections.add(websocket)
    client_info = websocket.remote_address
    print(f"[+] Client {connection_id} connected from {client_info[0]}:{client_info[1]}")
    print(f"[i] Active connections: {len(active_connections)}")

    try:
        # Keep connection until client disconnects
        async for message in websocket:
            print(f"[>] Received message from client {connection_id}: {message}")
            
            # Echo the message back to the client
            await websocket.send(message)
            print(f"[<] Echo message back to client {connection_id}")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"[!] Client {connection_id} connection closed: {e}")
    except Exception as e:
        print(f"[!] Error with client {connection_id}: {e}")
    finally:
        # Remove connection
        active_connections.remove(websocket)
        print(f"[-] Client {connection_id} disconnected")
        print(f"[i] Active connections: {len(active_connections)}")

def handle_shutdown(signal, frame):
    print("\n[!] Shutdown signal received. Closing server...")
    sys.exit(0)

async def main():
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Start WebSocket server
    server = await websockets.serve(handle_connection, HOST, PORT)
    print(f"[i] WebSocket Echo Server running on ws://{HOST}:{PORT}")
    print(f"[i] Press Ctrl+C to stop the server")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
EOF
fi

# Make the server script executable
chmod +x server.py

# Run the WebSocket server
echo "Starting WebSocket Echo Server on port 7070..."
python server.py 
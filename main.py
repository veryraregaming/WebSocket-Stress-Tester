# WebSocket Connection Tester - Progressive Stress Test

import asyncio
import websockets
import time
import argparse
import socket
import platform
import os
import psutil
import yaml

# Default configuration (fallback if config.yaml not found)
DEFAULT_CONFIG = {
    "server": {
        "host": "195.201.125.5",
        "port": 7070,
        "protocol": "ws",
        "path": "/"
    },
    "test": {
        "start_connections": 1,
        "max_connections": 10,
        "increment": 1,
        "batch_duration": 5,
        "connection_delay": 0,
        "stability_threshold": 90.0,
        "cumulative_mode": False  # Whether to keep previous connections active when adding new ones
    }
}

# Load configuration from YAML
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
            print(f"[ℹ️] Loaded configuration from {config_path}")
            return config
    except Exception as e:
        print(f"[⚠️] Warning: Could not load config.yaml ({str(e)}), using default configuration")
        return DEFAULT_CONFIG

# Global configuration
CONFIG = load_config()

def get_websocket_url(host, port, protocol, path):
    return f"{protocol}://{host}:{port}{path}"

def get_system_info():
    """Get basic system information for network troubleshooting context"""
    try:
        system_info = {
            "os": platform.system() + " " + platform.release(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "network_interfaces": []
        }
        
        # Get network interface information
        for interface, addresses in psutil.net_if_addrs().items():
            for address in addresses:
                if address.family == socket.AF_INET:  # IPv4
                    system_info["network_interfaces"].append({
                        "interface": interface,
                        "ip": address.address,
                        "netmask": address.netmask
                    })
        
        return system_info
    except Exception as e:
        return {"error": f"Could not gather system info: {str(e)}"}

def print_network_stats():
    """Print current network statistics"""
    try:
        net_stats = psutil.net_io_counters()
        print(f"Network Stats: Sent: {net_stats.bytes_sent/1024/1024:.2f} MB | Received: {net_stats.bytes_recv/1024/1024:.2f} MB")
        print(f"Packets: Sent: {net_stats.packets_sent} | Received: {net_stats.packets_recv} | Errors: {net_stats.errin + net_stats.errout}")
    except:
        print("Could not retrieve network statistics")

async def test_connection(i, url, connection_batch, end_event):
    """Test a single WebSocket connection and keep it open until the end event is set"""
    connection_id = i + 1
    start_time = time.time()
    response_times = []
    
    try:
        # CONNECT PHASE
        async with websockets.connect(url) as websocket:
            connected_time = time.time()
            connect_time = round((connected_time - start_time) * 1000, 2)  # in ms
            print(f"[✅] Batch {connection_batch} - Connection {connection_id} successfully connected ({connect_time}ms)")
            
            # INITIAL MESSAGE PHASE
            test_message = f"Test message from connection {connection_id}"
            message_start = time.time()
            await websocket.send(test_message)
            print(f"[📤] Batch {connection_batch} - Connection {connection_id} sent initial message")
            
            # Wait for response with timeout
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            message_time = round((time.time() - message_start) * 1000, 2)  # in ms
            response_times.append(message_time)
            print(f"[📥] Batch {connection_batch} - Connection {connection_id} received response: {message_time}ms")
            
            # HOLD CONNECTION OPEN PHASE - keep alive until the batch duration is up
            print(f"[⏱️] Batch {connection_batch} - Connection {connection_id} waiting for batch to complete...")
            
            check_interval = 1.0  # 1 second between checks
            
            # Keep connection open and test it periodically until end_event is set
            while not end_event.is_set():
                # Send a keepalive message while we wait
                keepalive_start = time.time()
                keepalive_msg = f"keepalive-{connection_id}"
                await websocket.send(keepalive_msg)
                
                # Wait for echo response
                echo_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_time = round((time.time() - keepalive_start) * 1000, 2)  # in ms
                response_times.append(response_time)
                print(f"[🔄] Batch {connection_batch} - Connection {connection_id} still active: {response_time}ms")
                
                # Wait for either the end event or check interval
                try:
                    await asyncio.wait_for(end_event.wait(), timeout=check_interval)
                except asyncio.TimeoutError:
                    # This is expected if the check_interval elapses before the event is set
                    pass
            
            print(f"[✓] Batch {connection_batch} - Connection {connection_id} completed batch test")
            
            return {
                "id": connection_id,
                "batch": connection_batch,
                "success": True,
                "duration": round(time.time() - start_time, 2),
                "connect_time": connect_time,
                "response_times": response_times,
                "avg_response": sum(response_times) / len(response_times) if response_times else 0,
                "min_response": min(response_times) if response_times else 0,
                "max_response": max(response_times) if response_times else 0,
                "error": None
            }
            
    except asyncio.TimeoutError:
        print(f"[❌] Batch {connection_batch} - Connection {connection_id} TIMED OUT waiting for response")
        return {
            "id": connection_id,
            "batch": connection_batch,
            "success": False,
            "duration": round(time.time() - start_time, 2),
            "error": "Timeout waiting for response"
        }
    except Exception as e:
        print(f"[❌] Batch {connection_batch} - Connection {connection_id} FAILED: {str(e)}")
        return {
            "id": connection_id,
            "batch": connection_batch,
            "success": False,
            "duration": round(time.time() - start_time, 2),
            "error": str(e)
        }

async def run_batch_test(num_connections, batch_number, websocket_url, connection_delay, batch_duration):
    """Run a batch of simultaneous connections for the specified batch duration"""
    print(f"\n[🔄] Starting batch {batch_number} with {num_connections} simultaneous connections")
    print(f"[⏱️] Batch will run for {batch_duration} seconds once all connections are established")
    if connection_delay > 0:
        print(f"[⏱️] Using {connection_delay}s delay between starting individual connections")
    print_network_stats()
    
    start_time = time.time()
    
    # Create an event to signal all connections to end
    end_event = asyncio.Event()
    
    # Create tasks with optional delay between each connection
    tasks = []
    for i in range(num_connections):
        task = asyncio.create_task(test_connection(i, websocket_url, batch_number, end_event))
        tasks.append(task)
        if connection_delay > 0 and i < num_connections - 1:
            await asyncio.sleep(connection_delay)
    
    # Wait for all connections to be established and then hold for batch duration
    print(f"\n[⏱️] All {num_connections} connections started, holding batch for {batch_duration} seconds...")
    await asyncio.sleep(batch_duration)
    
    # Signal all connections to end
    print(f"\n[⏱️] Batch {batch_number} duration complete, closing all connections...")
    end_event.set()
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Process results for this batch
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    # Calculate response time statistics
    all_response_times = []
    for result in successful:
        if "response_times" in result:
            all_response_times.extend(result["response_times"])
    
    avg_response = sum(all_response_times) / len(all_response_times) if all_response_times else 0
    min_response = min(all_response_times) if all_response_times else 0
    max_response = max(all_response_times) if all_response_times else 0
    
    batch_duration = round(time.time() - start_time, 2)
    
    # Print batch summary
    print(f"\n[📊] BATCH {batch_number} RESULTS:")
    print(f"Connections: {num_connections}")
    print(f"Successful: {len(successful)} ({len(successful)/num_connections*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/num_connections*100:.1f}%)")
    print(f"Response times: Avg: {avg_response:.2f}ms | Min: {min_response:.2f}ms | Max: {max_response:.2f}ms")
    print(f"Batch duration: {batch_duration}s")
    print_network_stats()
    
    if failed:
        print("\nFailed connections in this batch:")
        for result in failed:
            print(f"  Connection {result['id']}: {result['error']}")
    
    return {
        "batch": batch_number,
        "connections": num_connections,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful)/num_connections*100 if num_connections > 0 else 0,
        "avg_response": avg_response,
        "min_response": min_response,
        "max_response": max_response,
        "duration": batch_duration,
        "results": results
    }

async def main():
    # Load configuration
    config = CONFIG
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='WebSocket Connection Progressive Stress Tester')
    parser.add_argument('--host', default=config['server']['host'], help=f'WebSocket server hostname (default: {config["server"]["host"]})')
    parser.add_argument('--port', type=int, default=config['server']['port'], help=f'WebSocket server port (default: {config["server"]["port"]})')
    parser.add_argument('--protocol', default=config['server']['protocol'], choices=['ws', 'wss'], help=f'WebSocket protocol (default: {config["server"]["protocol"]})')
    parser.add_argument('--path', default=config['server']['path'], help=f'WebSocket endpoint path (default: {config["server"]["path"]})')
    parser.add_argument('--start', type=int, default=config['test']['start_connections'], help=f'Starting number of connections (default: {config["test"]["start_connections"]})')
    parser.add_argument('--max', type=int, default=config['test']['max_connections'], help=f'Maximum number of connections to test (default: {config["test"]["max_connections"]})')
    parser.add_argument('--increment', type=int, default=config['test']['increment'], help=f'How many connections to add in each batch (default: {config["test"]["increment"]})')
    parser.add_argument('--duration', type=int, default=config['test']['batch_duration'], help=f'How long to keep the entire batch open in seconds (default: {config["test"]["batch_duration"]})')
    parser.add_argument('--delay', type=float, default=config['test']['connection_delay'], help=f'Delay in seconds between starting individual connections (default: {config["test"]["connection_delay"]})')
    parser.add_argument('--cumulative', action='store_true', default=config['test']['cumulative_mode'], help=f'Cumulative mode: keep previous connections open when adding new ones')
    
    args = parser.parse_args()
    
    # Configure WebSocket URL and parameters
    websocket_url = get_websocket_url(args.host, args.port, args.protocol, args.path)
    start_connections = args.start
    max_connections = args.max
    connection_increment = args.increment
    batch_duration = args.duration
    stability_threshold = config['test']['stability_threshold']
    cumulative_mode = args.cumulative
    
    # Print test header
    print("="*80)
    print("PROGRESSIVE WEBSOCKET CONNECTION STRESS TEST")
    print("="*80)
    print(f"Target: {websocket_url}")
    print(f"Starting with {start_connections} connection(s), incrementing by {connection_increment}, up to {max_connections} max")
    print(f"Each batch will run for {batch_duration} seconds total")
    if cumulative_mode:
        print(f"CUMULATIVE MODE: Keeping existing connections open when adding new connections")
    if args.delay > 0:
        print(f"Using {args.delay}s delay between starting individual connections within each batch")
    
    # Print system information
    system_info = get_system_info()
    print("\nSYSTEM INFORMATION:")
    for key, value in system_info.items():
        if key != "network_interfaces":
            print(f"  {key}: {value}")
    
    print("\nNetwork Interfaces:")
    for interface in system_info.get("network_interfaces", []):
        print(f"  {interface['interface']}: {interface['ip']} ({interface['netmask']})")
    
    print("\nRunning test batches...")
    print("="*80)
    
    overall_start_time = time.time()
    batch_results = []
    
    # For cumulative mode - track all active tasks and end events
    all_active_tasks = []
    all_end_events = []
    
    # Run progressive tests
    batch_number = 1
    current_connections = start_connections
    total_connections = 0
    
    # Keep track of the last batch with a high success rate
    last_stable_batch = None
    
    while current_connections <= max_connections:
        if cumulative_mode:
            # In cumulative mode, we only create new connections equal to the increment
            # (or the start number for the first batch)
            num_new_connections = start_connections if batch_number == 1 else connection_increment
            total_connections += num_new_connections
            
            # Create end event for this batch
            end_event = asyncio.Event()
            all_end_events.append(end_event)
            
            # Create tasks for the new connections
            tasks = []
            for i in range(num_new_connections):
                # Use total_connections for global connection counting
                global_conn_id = total_connections - num_new_connections + i
                task = asyncio.create_task(test_connection(global_conn_id, websocket_url, batch_number, end_event))
                tasks.append(task)
                all_active_tasks.append(task)
                if args.delay > 0 and i < num_new_connections - 1:
                    await asyncio.sleep(args.delay)
            
            print(f"\n[🔄] Starting batch {batch_number} with {num_new_connections} new connections (total now: {total_connections})")
            print(f"[⏱️] Batch will run for {batch_duration} seconds")
            print_network_stats()
            
            # Wait for batch duration to test these new connections
            await asyncio.sleep(batch_duration)
            
            # Gather results for just this batch's new connections
            batch_results_only = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results for the new connections in this batch
            successful = [r for r in batch_results_only if isinstance(r, dict) and r.get("success", False)]
            failed = [r for r in batch_results_only if isinstance(r, dict) and not r.get("success", False)]
            
            success_rate = len(successful)/num_new_connections*100 if num_new_connections > 0 else 0
            
            # Print batch summary for the new connections
            print(f"\n[📊] BATCH {batch_number} NEW CONNECTIONS RESULTS:")
            print(f"New Connections: {num_new_connections}")
            print(f"Total Active Connections: {total_connections}")
            print(f"Successful: {len(successful)} ({success_rate:.1f}%)")
            print(f"Failed: {len(failed)} ({len(failed)/num_new_connections*100 if num_new_connections > 0 else 0:.1f}%)")
            print_network_stats()
            
            if failed:
                print("\nFailed connections in this batch:")
                for result in failed:
                    if isinstance(result, dict):
                        print(f"  Connection {result.get('id', 'unknown')}: {result.get('error', 'Unknown error')}")
                    else:
                        print(f"  Connection error: {str(result)}")
            
            batch_result = {
                "batch": batch_number,
                "new_connections": num_new_connections,
                "total_connections": total_connections,
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": success_rate
            }
            
            batch_results.append(batch_result)
            
            # Check if this batch is considered stable
            if success_rate >= stability_threshold:
                last_stable_batch = batch_result
            elif last_stable_batch is not None:
                # If we've had a stable batch before and this one failed, stop the test
                print(f"\n[⚠️] ERROR THRESHOLD REACHED - STOPPING TEST")
                print(f"     Batch {batch_number} with {num_new_connections} new connections (total: {total_connections}) shows degraded performance.")
                print(f"     Last stable batch was {last_stable_batch['batch']} with total {last_stable_batch['total_connections']} connections.")
                print(f"     Success rate for new connections dropped to {success_rate:.1f}% (below {stability_threshold}% threshold)")
                break
            
            # Move to next batch
            batch_number += 1
            current_connections += connection_increment
        else:
            # Original non-cumulative mode
            batch_result = await run_batch_test(current_connections, batch_number, websocket_url, args.delay, batch_duration)
            batch_results.append(batch_result)
            
            # Check if this batch is considered stable
            if batch_result["success_rate"] >= stability_threshold:
                last_stable_batch = batch_result
            elif last_stable_batch is not None:
                # If we've had a stable batch before and this one failed, stop the test
                print(f"\n[⚠️] ERROR THRESHOLD REACHED - STOPPING TEST")
                print(f"     Batch {batch_number} with {current_connections} connections shows degraded performance.")
                print(f"     Last stable batch was {last_stable_batch['batch']} with {last_stable_batch['connections']} connections.")
                print(f"     Success rate dropped to {batch_result['success_rate']:.1f}% (below {stability_threshold}% threshold)")
                break
            
            # Move to next batch
            batch_number += 1
            current_connections += connection_increment
        
        # Short pause between batches
        await asyncio.sleep(1)
    
    # Cleanup for cumulative mode - close all connections
    if cumulative_mode and all_end_events:
        print(f"\n[⏱️] Test complete, closing all {total_connections} connections...")
        # Signal all connections to end
        for event in all_end_events:
            event.set()
        
        # Wait for all tasks to complete
        if all_active_tasks:
            await asyncio.gather(*all_active_tasks, return_exceptions=True)
    
    # Print final summary
    overall_duration = round(time.time() - overall_start_time, 2)
    
    print("\n" + "="*80)
    print("FINAL TEST RESULTS")
    print("="*80)
    print(f"Target: {args.protocol}://{args.host}:{args.port}{args.path}")
    print(f"Test duration: {overall_duration} seconds")
    print(f"Batches completed: {len(batch_results)}")
    
    # Create a summary table - different for cumulative mode
    print("\nConnection Stability Summary:")
    print("-" * 100)
    
    if cumulative_mode:
        print(f"{'Batch #':<8} {'New Conns':<10} {'Total Conns':<12} {'Success Rate':<15} {'Status':<8}")
        print("-" * 100)
        
        for result in batch_results:
            success_rate = result.get('success_rate', 0)
            print(f"{result['batch']:<8} {result['new_connections']:<10} {result['total_connections']:<12} " + 
                  f"{success_rate:.1f}%{' ✓' if success_rate >= stability_threshold else ' ✗':<5}")
    else:
        print(f"{'Batch #':<8} {'Connections':<12} {'Success Rate':<15} {'Avg Response':<12} {'Min/Max (ms)':<15} {'Duration':<10}")
        print("-" * 100)
        
        for result in batch_results:
            print(f"{result['batch']:<8} {result['connections']:<12} {result['success_rate']:.1f}%{' ✓' if result['success_rate'] >= stability_threshold else ' ✗':<5} " + 
                  f"{result.get('avg_response', 0):.2f}ms{'':<6} {result.get('min_response', 0):.2f}/{result.get('max_response', 0):.2f}{'':<3} {result.get('duration', 0)}s")
    
    print("-" * 100)
    
    # Attempt to determine connection limit - different analysis for cumulative mode
    if cumulative_mode:
        stable_batches = [r for r in batch_results if r['success_rate'] >= stability_threshold]
        unstable_batches = [r for r in batch_results if r['success_rate'] < stability_threshold]
        
        if unstable_batches:
            if stable_batches:
                max_stable = max(stable_batches, key=lambda x: x['total_connections'])
                min_unstable = min(unstable_batches, key=lambda x: x['total_connections'])
                
                print(f"\nConnection Stability Analysis (Cumulative Mode):")
                print(f"✅ Maximum STABLE total connections: {max_stable['total_connections']} (Batch {max_stable['batch']}, {max_stable['success_rate']:.1f}% success)")
                print(f"❌ Minimum UNSTABLE total connections: {min_unstable['total_connections']} (Batch {min_unstable['batch']}, {min_unstable['success_rate']:.1f}% success)")
                
                if min_unstable['total_connections'] - max_stable['total_connections'] <= connection_increment:
                    print(f"\n🎯 The system appears to handle around {max_stable['total_connections']} cumulative WebSocket connections.")
                    print(f"   When adding more to reach {min_unstable['total_connections']} connections, new connections began to fail.")
                else:
                    print(f"\n🎯 The system's connection handling threshold is between {max_stable['total_connections']} and {min_unstable['total_connections']} total connections.")
                    print(f"   Consider running a more precise test in this range with smaller increments.")
            else:
                print(f"\n❌ All tests showed connection instability. The system may have issues even with {batch_results[0]['total_connections']} connections.")
        else:
            if batch_results:
                max_tested = max(batch_results, key=lambda x: x['total_connections'])
                print(f"\n✅ All connection batches were STABLE up to {max_tested['total_connections']} total connections.")
                print(f"   The system can handle at least {max_tested['total_connections']} simultaneous WebSocket connections.")
                print(f"   Consider running a test with more connections to find the limit.")
            else:
                print("\nNo test results available.")
    else:
        # Original non-cumulative analysis
        stable_connections = [r for r in batch_results if r['success_rate'] >= stability_threshold]
        unstable_connections = [r for r in batch_results if r['success_rate'] < stability_threshold]
        
        if unstable_connections:
            if stable_connections:
                max_stable = max(stable_connections, key=lambda x: x['connections'])
                min_unstable = min(unstable_connections, key=lambda x: x['connections'])
                
                print(f"\nConnection Stability Analysis:")
                print(f"✅ Maximum STABLE connections: {max_stable['connections']} (Batch {max_stable['batch']}, {max_stable['success_rate']:.1f}% success)")
                print(f"❌ Minimum UNSTABLE connections: {min_unstable['connections']} (Batch {min_unstable['batch']}, {min_unstable['success_rate']:.1f}% success)")
                
                if min_unstable['connections'] - max_stable['connections'] <= connection_increment:
                    print(f"\n🎯 Your connection appears to handle around {max_stable['connections']} simultaneous WebSocket connections.")
                    print(f"   When increasing to {min_unstable['connections']} connections, stability began to deteriorate.")
                else:
                    print(f"\n🎯 Your connection stability threshold is between {max_stable['connections']} and {min_unstable['connections']} simultaneous connections.")
                    print(f"   Consider running a more precise test in this range with smaller increments.")
            else:
                print(f"\n❌ All tests showed connection instability. Your connection may not support even {start_connections} simultaneous WebSocket connections.")
        else:
            if batch_results:
                max_tested = max(batch_results, key=lambda x: x['connections'])
                print(f"\n✅ All tests were STABLE up to {max_tested['connections']} simultaneous connections.")
                print(f"   Your connection can handle at least {max_tested['connections']} simultaneous WebSocket connections.")
                print(f"   Consider running a test with more connections to find your limit.")
            else:
                print("\nNo test results available.")
    
    print("\nPossible factors affecting connection stability:")
    print("- Internet service provider bandwidth and quality")
    print("- Router/modem capabilities and configuration")
    print("- Network congestion or throttling")
    print("- Server capacity and responsiveness")
    print("- Operating system network stack limitations")
    
    print("="*80)

if __name__ == "__main__":
    # Check for dependencies
    try:
        import psutil
    except ImportError:
        print("The 'psutil' module is required. Installing...")
        try:
            import subprocess
            subprocess.check_call(["pip", "install", "psutil"])
            import psutil
            print("Successfully installed psutil.")
        except Exception as e:
            print(f"Error installing psutil: {e}")
            print("Please install it manually with: pip install psutil")
            exit(1)
    
    asyncio.run(main())

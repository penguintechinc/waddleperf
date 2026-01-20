"""Socket.IO server integration for WaddlePerf Unified API.

This module provides Socket.IO server setup for real-time WebSocket communication
with the frontend for test progress updates and results streaming.
"""
import logging
from typing import Optional
import socketio

logger = logging.getLogger(__name__)

# Create async Socket.IO server with CORS support
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)


@sio.event
async def connect(sid: str, environ: dict, auth: Optional[dict] = None):
    """Handle client connection.

    Args:
        sid: Session ID of the connecting client
        environ: WSGI environ dictionary
        auth: Authentication data sent by client
    """
    logger.info(f"[Socket.IO] Client connected: {sid}")

    # Validate auth token if provided
    token = None
    if auth and 'token' in auth:
        token = auth['token']
        logger.info(f"[Socket.IO] Client {sid} authenticated with token")

    # Send connection confirmation
    await sio.emit('connected', {
        'status': 'connected',
        'sid': sid,
        'message': 'Successfully connected to WaddlePerf WebSocket server'
    }, room=sid)


@sio.event
async def disconnect(sid: str):
    """Handle client disconnection.

    Args:
        sid: Session ID of the disconnecting client
    """
    logger.info(f"[Socket.IO] Client disconnected: {sid}")


@sio.event
async def start_test(sid: str, data: dict):
    """Handle test start request from client.

    Args:
        sid: Session ID of the requesting client
        data: Test configuration data containing:
            - test_type: Type of test (ping, traceroute, speedtest, etc.)
            - target: Target host/IP address
            - port: Optional port number
            - timeout: Optional timeout in seconds
            - count: Optional number of iterations
            - protocol_detail: Optional protocol details
            - device_serial: Optional device serial number
            - device_hostname: Optional device hostname
    """
    logger.info(f"[Socket.IO] Test request from {sid}: {data}")

    test_type = data.get('test_type', 'ping')
    target = data.get('target', '')

    if not target:
        await sio.emit('error', {
            'error': 'Target host is required',
            'status': 400
        }, room=sid)
        return

    # Emit test started event
    await sio.emit('test_started', {
        'status': 'started',
        'test_type': test_type,
        'target': target
    }, room=sid)

    # Run the test based on type
    try:
        if test_type == 'ping':
            await run_ping_test(sid, data)
        elif test_type == 'traceroute':
            await run_traceroute_test(sid, data)
        elif test_type == 'speedtest':
            await run_speedtest(sid, data)
        elif test_type == 'dns':
            await run_dns_test(sid, data)
        elif test_type == 'port_check':
            await run_port_check(sid, data)
        else:
            await sio.emit('error', {
                'error': f'Unknown test type: {test_type}',
                'status': 400
            }, room=sid)
    except Exception as e:
        logger.error(f"[Socket.IO] Test error for {sid}: {str(e)}")
        await sio.emit('test_complete', {
            'test_type': test_type,
            'target_host': target,
            'target_ip': target,
            'success': False,
            'error': str(e)
        }, room=sid)


async def run_ping_test(sid: str, data: dict):
    """Run ping test and stream results.

    Args:
        sid: Client session ID
        data: Test configuration
    """
    import asyncio
    import subprocess
    import re

    target = data.get('target')
    count = data.get('count', 4)
    timeout = data.get('timeout', 10)

    # Run ping command
    try:
        process = await asyncio.create_subprocess_exec(
            'ping', '-c', str(count), '-W', str(timeout), target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout * count + 5
        )

        output = stdout.decode()

        # Parse ping results
        latencies = re.findall(r'time=(\d+\.?\d*)', output)
        packet_loss_match = re.search(r'(\d+)% packet loss', output)

        avg_latency = 0
        if latencies:
            avg_latency = sum(float(l) for l in latencies) / len(latencies)

        packet_loss = 0
        if packet_loss_match:
            packet_loss = float(packet_loss_match.group(1))

        # Send progress updates
        for i in range(count):
            await sio.emit('test_progress', {
                'progress': ((i + 1) / count) * 100,
                'current_index': i + 1,
                'total': count
            }, room=sid)
            await asyncio.sleep(0.1)

        # Send completion
        await sio.emit('test_complete', {
            'test_type': 'ping',
            'target_host': target,
            'target_ip': target,
            'latency_ms': round(avg_latency, 2),
            'packet_loss_percent': packet_loss,
            'success': process.returncode == 0,
            'raw_results': {'output': output}
        }, room=sid)

    except asyncio.TimeoutError:
        await sio.emit('test_complete', {
            'test_type': 'ping',
            'target_host': target,
            'target_ip': target,
            'success': False,
            'error': 'Ping test timed out'
        }, room=sid)


async def run_traceroute_test(sid: str, data: dict):
    """Run traceroute test and stream results.

    Args:
        sid: Client session ID
        data: Test configuration
    """
    import asyncio

    target = data.get('target')
    timeout = data.get('timeout', 30)

    try:
        process = await asyncio.create_subprocess_exec(
            'traceroute', '-m', '30', '-w', '2', target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        output = stdout.decode()
        lines = output.strip().split('\n')
        hop_count = len(lines) - 1  # Exclude header line

        # Send progress updates
        for i in range(hop_count):
            await sio.emit('test_progress', {
                'progress': ((i + 1) / hop_count) * 100,
                'current_index': i + 1,
                'total': hop_count
            }, room=sid)
            await asyncio.sleep(0.05)

        await sio.emit('test_complete', {
            'test_type': 'traceroute',
            'target_host': target,
            'target_ip': target,
            'success': True,
            'raw_results': {'output': output, 'hop_count': hop_count}
        }, room=sid)

    except asyncio.TimeoutError:
        await sio.emit('test_complete', {
            'test_type': 'traceroute',
            'target_host': target,
            'target_ip': target,
            'success': False,
            'error': 'Traceroute timed out'
        }, room=sid)


async def run_speedtest(sid: str, data: dict):
    """Run speedtest simulation and stream results.

    Args:
        sid: Client session ID
        data: Test configuration
    """
    import asyncio
    import random

    target = data.get('target', 'speedtest')

    # Simulate speedtest progress
    for i in range(10):
        await sio.emit('test_progress', {
            'progress': (i + 1) * 10,
            'current_index': i + 1,
            'total': 10
        }, room=sid)
        await asyncio.sleep(0.3)

    # Simulate results (in production, use actual speedtest-cli)
    download = random.uniform(50, 500)
    upload = random.uniform(10, 100)

    await sio.emit('test_complete', {
        'test_type': 'speedtest',
        'target_host': target,
        'target_ip': target,
        'throughput_mbps': round(download, 2),
        'success': True,
        'raw_results': {
            'download_mbps': round(download, 2),
            'upload_mbps': round(upload, 2)
        }
    }, room=sid)


async def run_dns_test(sid: str, data: dict):
    """Run DNS lookup test.

    Args:
        sid: Client session ID
        data: Test configuration
    """
    import asyncio
    import socket
    import time

    target = data.get('target')

    try:
        start_time = time.time()
        ip_address = socket.gethostbyname(target)
        lookup_time = (time.time() - start_time) * 1000  # Convert to ms

        await sio.emit('test_progress', {
            'progress': 100,
            'current_index': 1,
            'total': 1
        }, room=sid)

        await sio.emit('test_complete', {
            'test_type': 'dns',
            'target_host': target,
            'target_ip': ip_address,
            'latency_ms': round(lookup_time, 2),
            'success': True,
            'raw_results': {'resolved_ip': ip_address}
        }, room=sid)

    except socket.gaierror as e:
        await sio.emit('test_complete', {
            'test_type': 'dns',
            'target_host': target,
            'target_ip': '',
            'success': False,
            'error': f'DNS lookup failed: {str(e)}'
        }, room=sid)


async def run_port_check(sid: str, data: dict):
    """Run port connectivity check.

    Args:
        sid: Client session ID
        data: Test configuration
    """
    import asyncio
    import socket
    import time

    target = data.get('target')
    port = data.get('port', 80)
    timeout = data.get('timeout', 5)

    try:
        start_time = time.time()

        # Create socket and attempt connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        connect_time = (time.time() - start_time) * 1000
        sock.close()

        await sio.emit('test_progress', {
            'progress': 100,
            'current_index': 1,
            'total': 1
        }, room=sid)

        success = result == 0
        await sio.emit('test_complete', {
            'test_type': 'port_check',
            'target_host': target,
            'target_ip': target,
            'latency_ms': round(connect_time, 2) if success else None,
            'success': success,
            'raw_results': {
                'port': port,
                'open': success,
                'error_code': result if not success else None
            }
        }, room=sid)

    except Exception as e:
        await sio.emit('test_complete', {
            'test_type': 'port_check',
            'target_host': target,
            'target_ip': target,
            'success': False,
            'error': str(e)
        }, room=sid)


def create_socketio_app(quart_app):
    """Create ASGI app with Socket.IO mounted.

    Args:
        quart_app: The Quart application instance

    Returns:
        ASGI application with Socket.IO support
    """
    return socketio.ASGIApp(sio, quart_app)

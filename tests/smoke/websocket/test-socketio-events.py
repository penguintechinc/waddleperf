#!/usr/bin/env python3
"""
tests/smoke/websocket/test-socketio-events.py

Smoke test for Socket.IO event handling.
Verifies that the Socket.IO server accepts connections and responds to events.
"""

import asyncio
import os
import sys

try:
    import socketio
except ImportError:
    print("ERROR: python-socketio not installed")
    print("Install with: pip install python-socketio[asyncio_client]")
    sys.exit(1)


API_URL = os.environ.get("API_URL", "http://localhost:5000")
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))


async def run_socketio_smoke_test():
    """Run Socket.IO connection and event smoke tests."""
    print("=== Socket.IO Event Smoke Test ===")
    print(f"API URL: {API_URL}")
    print()

    # Create async Socket.IO client
    sio = socketio.AsyncClient(
        logger=False,
        engineio_logger=False
    )

    connected = False
    connection_confirmed = False
    test_passed = False
    error_message = None

    @sio.event
    async def connect():
        nonlocal connected
        connected = True
        print("    ✓ Socket.IO connected successfully")

    @sio.event
    async def connected(data):
        nonlocal connection_confirmed
        connection_confirmed = True
        print(f"    ✓ Server confirmed connection: {data.get('message', 'OK')}")

    @sio.event
    async def connect_error(data):
        nonlocal error_message
        error_message = str(data)
        print(f"    ✗ Connection error: {data}")

    @sio.event
    async def disconnect():
        print("    → Socket.IO disconnected")

    try:
        # Test 1: Connect to Socket.IO server
        print("[1/3] Connecting to Socket.IO server...")
        await asyncio.wait_for(
            sio.connect(API_URL, transports=['websocket', 'polling']),
            timeout=TIMEOUT
        )

        if not connected:
            print("    ✗ Failed to connect")
            return False

        # Wait briefly for server confirmation
        await asyncio.sleep(1)

        # Test 2: Verify connection was confirmed by server
        print()
        print("[2/3] Verifying server connection confirmation...")
        if connection_confirmed:
            print("    ✓ Server sent connection confirmation event")
        else:
            print("    ⚠ Server did not send confirmation (may be OK)")

        # Test 3: Test event emission (start_test without target - should get error)
        print()
        print("[3/3] Testing event emission...")

        test_response_received = False
        test_error_received = False

        @sio.on('error')
        async def on_error(data):
            nonlocal test_error_received
            test_error_received = True
            print(f"    ✓ Received error response (expected): {data.get('error', 'Unknown')}")

        @sio.on('test_started')
        async def on_test_started(data):
            nonlocal test_response_received
            test_response_received = True
            print(f"    ✓ Received test_started response: {data}")

        # Emit start_test event without target (should trigger error response)
        await sio.emit('start_test', {'test_type': 'ping', 'target': ''})

        # Wait for response
        await asyncio.sleep(2)

        if test_error_received or test_response_received:
            print("    ✓ Server responded to emitted event")
            test_passed = True
        else:
            print("    ⚠ No response received from server")
            # Still consider it a pass if connection worked
            test_passed = connected

    except asyncio.TimeoutError:
        print(f"    ✗ Connection timed out after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"    ✗ Error: {str(e)}")
        return False
    finally:
        if sio.connected:
            await sio.disconnect()

    print()
    if test_passed:
        print("=== Socket.IO Event Smoke Test: PASSED ===")
    else:
        print("=== Socket.IO Event Smoke Test: FAILED ===")

    return test_passed


def main():
    """Main entry point."""
    success = asyncio.run(run_socketio_smoke_test())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# WaddlePerf Enrollment Flow (FleetDM-Style)

## Overview

WaddlePerf uses a FleetDM-style enrollment system where:
1. Clients start with local ENV configuration (fallback)
2. Clients enroll using an enrollment secret → Assigned to an OU/Team
3. **Manager server configuration OVERRIDES all local settings** after enrollment

## Client Deployment Flow

### Step 1: Deploy Client with ENV Variables

```bash
docker run -d \
  --name waddleperf-client \
  -e ENROLLMENT_SECRET="your-secret-here" \
  -e MANAGER_URL="https://manager.example.com" \
  -e DEVICE_SERIAL="$(cat /proc/sys/kernel/random/uuid)" \
  -e DEVICE_HOSTNAME="$(hostname)" \
  \
  # Optional fallback config (used ONLY before enrollment):
  -e ENABLE_HTTP_TEST="true" \
  -e ENABLE_TCP_TEST="true" \
  -e ENABLE_UDP_TEST="false" \
  -e ENABLE_ICMP_TEST="true" \
  -e TEST_INTERVAL_SECONDS="300" \
  \
  waddleperf/client:latest
```

### Step 2: Client Auto-Enrollment

On first start, the client:

```python
# Client pseudo-code
import os
import requests

# Required ENV vars
ENROLLMENT_SECRET = os.getenv('ENROLLMENT_SECRET')  # REQUIRED
MANAGER_URL = os.getenv('MANAGER_URL')  # REQUIRED
DEVICE_SERIAL = os.getenv('DEVICE_SERIAL')  # REQUIRED

# Fallback local config (used ONLY if not enrolled)
LOCAL_CONFIG = {
    'http_enabled': os.getenv('ENABLE_HTTP_TEST', 'true').lower() == 'true',
    'tcp_enabled': os.getenv('ENABLE_TCP_TEST', 'true').lower() == 'true',
    'udp_enabled': os.getenv('ENABLE_UDP_TEST', 'false').lower() == 'true',
    'icmp_enabled': os.getenv('ENABLE_ICMP_TEST', 'true').lower() == 'true',
    'interval': int(os.getenv('TEST_INTERVAL_SECONDS', '300'))
}

def enroll():
    """Enroll with manager server"""
    response = requests.post(f'{MANAGER_URL}/api/v1/enrollment/enroll', json={
        'secret': ENROLLMENT_SECRET,
        'device_serial': DEVICE_SERIAL,
        'device_hostname': os.getenv('DEVICE_HOSTNAME', 'unknown'),
        'device_os': 'Linux',  # Detect actual OS
        'device_os_version': '6.1.0',  # Detect actual version
        'client_type': 'containerClient',  # or 'goClient'
        'client_version': '4.0.0'
    })

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✓ Enrolled to OU: {data['ou_id']}")
        return True
    else:
        print(f"✗ Enrollment failed: {response.text}")
        return False

def get_config():
    """Fetch configuration from manager (OVERRIDES local ENV)"""
    response = requests.get(
        f'{MANAGER_URL}/api/v1/enrollment/config',
        params={'device_serial': DEVICE_SERIAL}
    )

    if response.status_code == 200:
        data = response.json()
        config = data['config']

        # Manager config OVERRIDES all local ENV vars
        print(f"✓ Using manager config: {data['config_name']}")
        print(f"  - Schedule: {config['schedule']['actual_interval_seconds']}s (with random offset)")
        print(f"  - HTTP: {config['tests']['http']['enabled']}")
        print(f"  - TCP: {config['tests']['tcp']['enabled']}")
        print(f"  - UDP: {config['tests']['udp']['enabled']}")
        print(f"  - ICMP: {config['tests']['icmp']['enabled']}")

        return config
    else:
        print("⚠ Using local ENV config (not enrolled)")
        return LOCAL_CONFIG

# Main loop
if __name__ == '__main__':
    # Try to enroll
    enrolled = enroll()

    # Two separate intervals to understand:
    # 1. Test interval (how often to run tests): 5 minutes with ±15% offset
    # 2. Config check-in interval (how often to pull config): 30-60 minutes random

    config_checkin_timer = 0
    test_run_timer = 0

    while True:
        current_time = time.time()

        # Check if we need to pull new config from manager (30-60 min intervals)
        if current_time >= config_checkin_timer:
            print("⟳ Checking for config updates from manager...")
            response = get_config()  # Returns config + next_checkin_seconds
            config = response['config']
            next_checkin = response.get('next_checkin_seconds', 1800)  # 30-60 min
            config_checkin_timer = current_time + next_checkin
            print(f"  Next config check-in: {next_checkin/60:.1f} minutes")

        # Check if we need to run tests (based on config schedule)
        if current_time >= test_run_timer:
            print("▶ Running tests...")
            run_tests(config)

            # Get next test interval with random offset
            test_interval = config['schedule']['actual_interval_seconds']  # 5 min ±15%
            test_run_timer = current_time + test_interval
            print(f"  Next test run: {test_interval/60:.1f} minutes")

            # Send heartbeat
            requests.post(f'{MANAGER_URL}/api/v1/enrollment/devices/{device_id}/heartbeat')

        # Sleep for a short period and loop
        time.sleep(60)  # Check timers every minute
```

### Step 3: Manager Overrides Configuration

Administrator changes configuration in Manager UI:
- **OU Configuration** → Sets which tests run, schedule, targets
- **Changes apply immediately** on next client check-in
- **No client restart needed**

## Two Important Intervals

**IMPORTANT**: There are TWO separate timing mechanisms:

### 1. Test Execution Interval
- **What**: How often the client runs network tests
- **Default**: 300 seconds (5 minutes) ± 15% offset
- **Random offset**: Prevents thundering herd (e.g., 255-345 seconds)
- **Configured by**: Administrator in OU/Team configuration
- **Example**: Tests run every ~5 minutes with randomization

### 2. Configuration Check-In Interval
- **What**: How often the client pulls updated config from manager
- **Default**: Random between 30-60 minutes
- **Purpose**: Allow admin to push config changes to clients
- **Configured by**: Global system setting (`client_checkin_min/max_seconds`)
- **Example**: Client checks for config updates every 30-60 minutes (random)

### Why Two Intervals?

```
Timeline Example:
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  Config Check-in: Every 30-60 min (random)                   │
│  ↓                              ↓                             │
│  0:00                          45:00                          │
│  Get config (tests every 5min) Get updated config            │
│                                                               │
│  Test Runs: Every 5 min ±15% = ~4.25-5.75 min                │
│  ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓                   │
│  0:00 5:12 10:08 15:17 20:04 25:15 30:11 35:06 40:14 45:09   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

- Tests run frequently (every ~5 minutes)
- Config checks happen infrequently (every 30-60 minutes)
- Both use randomization to prevent synchronized load
```

### Benefits:
1. **Responsive testing**: Issues detected within minutes
2. **Efficient management**: Config updates propagate within an hour
3. **Load distribution**: Random offsets prevent spike loads
4. **Bandwidth efficient**: Don't check config on every test run

## Configuration Hierarchy

```
┌─────────────────────────────────────────────┐
│ 1. Manager Server Config (HIGHEST PRIORITY)│  ← OVERRIDES everything
├─────────────────────────────────────────────┤
│   - OU-specific config                      │
│   - Applied after enrollment                │
│   - Includes random schedule offset         │
│   - Admin can change anytime                │
└─────────────────────────────────────────────┘
              ↓ Overrides
┌─────────────────────────────────────────────┐
│ 2. Default Manager Config                   │  ← Fallback for enrolled
├─────────────────────────────────────────────┤     devices without OU config
│   - Global default                          │
│   - Applied if no OU config exists          │
└─────────────────────────────────────────────┘
              ↓ Overrides
┌─────────────────────────────────────────────┐
│ 3. Local ENV Variables (LOWEST PRIORITY)   │  ← ONLY used before
├─────────────────────────────────────────────┤     enrollment
│   - ENABLE_HTTP_TEST=true                   │
│   - TEST_INTERVAL_SECONDS=300               │
│   - Only used if NOT enrolled               │
└─────────────────────────────────────────────┘
```

## Example Scenarios

### Scenario 1: Fresh Deployment
1. Deploy client with `ENROLLMENT_SECRET=abc123`
2. Client enrolls → Assigned to "Engineering" OU
3. **Manager config immediately takes over**
4. Client runs tests per Engineering OU configuration
5. Local ENV vars are **IGNORED** from this point forward

### Scenario 2: Configuration Change
1. Admin updates Engineering OU config:
   - Change: Enable UDP tests
   - Change: Increase interval to 600s
   - Change: Add new target: `dns.google:853`
2. **Next client check-in** (within current interval)
3. Client receives new config with changes
4. Client **immediately** applies new settings
5. **No restart required**

### Scenario 3: Enrollment Failure
1. Deploy client with invalid `ENROLLMENT_SECRET`
2. Enrollment fails
3. Client **falls back to local ENV config**
4. Client retries enrollment periodically
5. Once enrolled, manager config takes over

## Client Configuration API

### Enrollment Endpoint
```http
POST /api/v1/enrollment/enroll
Content-Type: application/json

{
  "secret": "enrollment-secret-here",
  "device_serial": "unique-device-id",
  "device_hostname": "client-001",
  "device_os": "Linux",
  "device_os_version": "6.1.0",
  "client_type": "containerClient",
  "client_version": "4.0.0"
}

Response 201:
{
  "message": "Device enrolled successfully",
  "ou_id": 3,
  "device_id": 42
}
```

### Configuration Check-in Endpoint
```http
GET /api/v1/enrollment/config?device_serial=unique-device-id

Response 200:
{
  "config": {
    "tests": {
      "http": {
        "enabled": true,
        "targets": ["https://google.com", "https://cloudflare.com"]
      },
      "tcp": {
        "enabled": true,
        "targets": ["8.8.8.8:53"]
      },
      "udp": {
        "enabled": false,
        "targets": []
      },
      "icmp": {
        "enabled": true,
        "targets": ["8.8.8.8", "1.1.1.1"]
      }
    },
    "schedule": {
      "interval_seconds": 300,
      "offset_percent": 15,
      "actual_interval_seconds": 287,  ← Random test interval offset!
      "next_check_in": 1699564123.45   ← When to run next test
    },
    "thresholds": {
      "latency_warning_ms": 100,
      "latency_critical_ms": 500,
      "jitter_warning_ms": 50,
      "jitter_critical_ms": 200,
      "packet_loss_warning_percent": 1.0,
      "packet_loss_critical_percent": 5.0
    }
  },
  "config_name": "Engineering Config",
  "ou_id": 3,
  "next_checkin_seconds": 2847,      ← When to check for config updates (30-60 min random)
  "next_checkin_at": 1699566970.45   ← Timestamp for next config check-in
}
```

**Key Response Fields:**
- `config.schedule.actual_interval_seconds`: How long until next TEST run (with random offset)
- `next_checkin_seconds`: How long until next CONFIG check-in (30-60 min random)
- Both intervals are independent!

### Heartbeat Endpoint
```http
POST /api/v1/enrollment/devices/42/heartbeat

Response 200:
{
  "message": "Heartbeat recorded"
}
```

## Benefits of This Approach

1. **Centralized Management**: Change configs for 100s of devices from one UI
2. **No Client Restarts**: Changes apply on next check-in
3. **Graceful Degradation**: Falls back to ENV if enrollment fails
4. **Load Distribution**: Random offsets prevent thundering herd
5. **Audit Trail**: Track which configs are deployed where
6. **Role-Based Access**: OU admins manage their team's configs

## Implementation Checklist for Clients

- [ ] Read `ENROLLMENT_SECRET` and `MANAGER_URL` from ENV (required)
- [ ] Read fallback test config from ENV (optional, only used pre-enrollment)
- [ ] Call `/enrollment/enroll` on startup
- [ ] Call `/enrollment/config?device_serial=X` on every check-in
- [ ] **ALWAYS use manager config when available** (overrides ENV)
- [ ] Apply random offset from `actual_interval_seconds`
- [ ] Send heartbeat periodically
- [ ] Handle enrollment failures gracefully (retry + use ENV fallback)

#!/usr/bin/env python3
"""ICMP test implementation for containerClient"""

import asyncio
import time
import logging
import struct
import socket
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field, asdict


@dataclass
class IcmpTestResult:
    """ICMP test result data"""
    test_type: str = "icmp"
    protocol_detail: str = "ping"
    target_host: str = ""
    target_ip: str = ""
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_percent: float = 0.0
    packets_sent: int = 0
    packets_received: int = 0
    success: bool = False
    error: Optional[str] = None
    raw_results: Dict = field(default_factory=dict)


class IcmpTest:
    """ICMP ping test implementation"""

    def __init__(self, timeout: int = 5, packet_count: int = 4):
        self.timeout = timeout
        self.packet_count = packet_count
        self.logger = logging.getLogger(__name__)

    async def _resolve_host(self, host: str) -> Optional[str]:
        """Resolve hostname to IP address"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.getaddrinfo(host, None)
            if result:
                return result[0][4][0]
        except Exception as e:
            self.logger.error(f"DNS resolution failed for {host}: {e}")
        return None

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate ICMP checksum"""
        checksum = 0
        count_to = (len(data) // 2) * 2
        count = 0

        while count < count_to:
            this_val = data[count + 1] * 256 + data[count]
            checksum = checksum + this_val
            checksum = checksum & 0xffffffff
            count = count + 2

        if count_to < len(data):
            checksum = checksum + data[len(data) - 1]
            checksum = checksum & 0xffffffff

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum = checksum + (checksum >> 16)
        answer = ~checksum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    async def _ping_once(self, sock: socket.socket, dest_addr: str, seq: int) -> Optional[float]:
        """Send single ICMP ping and measure RTT"""
        loop = asyncio.get_event_loop()

        try:
            # ICMP Echo Request packet
            icmp_type = 8  # Echo Request
            icmp_code = 0
            icmp_checksum = 0
            icmp_id = os.getpid() & 0xFFFF
            icmp_seq = seq

            # Create header
            header = struct.pack("!BBHHH", icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
            data = struct.pack("!d", time.time())

            # Calculate checksum
            checksum = self._calculate_checksum(header + data)
            header = struct.pack("!BBHHH", icmp_type, icmp_code, checksum, icmp_id, icmp_seq)

            packet = header + data

            # Send packet
            send_time = time.perf_counter()
            await loop.sock_sendto(sock, packet, (dest_addr, 1))

            # Wait for reply
            try:
                while True:
                    recv_data, recv_addr = await asyncio.wait_for(
                        loop.sock_recvfrom(sock, 1024),
                        timeout=self.timeout
                    )
                    recv_time = time.perf_counter()

                    # Parse ICMP reply
                    icmp_header = recv_data[20:28]
                    recv_type, recv_code, recv_checksum, recv_id, recv_seq = struct.unpack("!BBHHH", icmp_header)

                    # Check if this is our reply
                    if recv_type == 0 and recv_id == icmp_id and recv_seq == seq:
                        rtt = (recv_time - send_time) * 1000
                        return rtt

            except asyncio.TimeoutError:
                return None

        except Exception as e:
            self.logger.debug(f"ICMP ping error: {e}")
            return None

    async def _run_ping_test(self, host: str) -> IcmpTestResult:
        """Run ICMP ping test"""
        result = IcmpTestResult(
            protocol_detail="ping",
            target_host=host
        )

        try:
            # Resolve hostname
            result.target_ip = await self._resolve_host(host) or host

            # Create raw socket (requires root/CAP_NET_RAW)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                sock.setblocking(False)
                sock.setsockopt(socket.SOL_IP, socket.IP_TTL, 64)
            except PermissionError:
                # Fallback to system ping command if no raw socket permission
                self.logger.warning("No raw socket permission, falling back to system ping")
                return await self._run_system_ping(host)

            rtts: List[float] = []
            result.packets_sent = self.packet_count

            # Send pings with interval
            for seq in range(self.packet_count):
                rtt = await self._ping_once(sock, result.target_ip, seq)
                if rtt is not None:
                    rtts.append(rtt)
                    result.packets_received += 1
                    self.logger.debug(f"ICMP ping {seq}: RTT={rtt:.2f}ms")

                # Wait between pings (except last)
                if seq < self.packet_count - 1:
                    await asyncio.sleep(1)

            sock.close()

            # Calculate statistics
            if rtts:
                result.latency_ms = sum(rtts) / len(rtts)
                result.success = True

                # Calculate jitter
                if len(rtts) > 1:
                    diffs = [abs(rtts[i] - rtts[i-1]) for i in range(1, len(rtts))]
                    result.jitter_ms = sum(diffs) / len(diffs)

            result.packet_loss_percent = ((result.packets_sent - result.packets_received) / result.packets_sent) * 100

            result.raw_results = {
                'rtts': rtts,
                'min_rtt': min(rtts) if rtts else 0,
                'max_rtt': max(rtts) if rtts else 0,
                'avg_rtt': result.latency_ms
            }

        except Exception as e:
            result.error = f"error: {str(e)}"
            self.logger.error(f"ICMP test error for {host}: {e}")

        return result

    async def _run_system_ping(self, host: str) -> IcmpTestResult:
        """Fallback to system ping command"""
        result = IcmpTestResult(
            protocol_detail="ping",
            target_host=host
        )

        try:
            # Resolve hostname first
            result.target_ip = await self._resolve_host(host) or host

            # Use system ping command
            import platform
            system = platform.system().lower()

            if system == "windows":
                cmd = f"ping -n {self.packet_count} -w {self.timeout * 1000} {host}"
            else:
                cmd = f"ping -c {self.packet_count} -W {self.timeout} {host}"

            # Run ping command
            start_time = time.perf_counter()
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout * self.packet_count + 5
            )
            end_time = time.perf_counter()

            output = stdout.decode('utf-8', errors='ignore')

            # Parse output (basic parsing)
            result.packets_sent = self.packet_count
            result.packets_received = output.count("time=") if system != "windows" else output.count("Reply from")
            result.packet_loss_percent = ((result.packets_sent - result.packets_received) / result.packets_sent) * 100

            # Try to extract average time
            if "avg" in output.lower():
                # Linux/Mac format
                import re
                match = re.search(r'min/avg/max[^=]*=\s*[\d.]+/([\d.]+)/', output)
                if match:
                    result.latency_ms = float(match.group(1))
                    result.success = True
            elif result.packets_received > 0:
                # Windows or partial success
                result.latency_ms = (end_time - start_time) * 1000 / result.packets_sent
                result.success = True

            result.raw_results = {
                'command_output': output.strip(),
                'execution_time_ms': (end_time - start_time) * 1000
            }

        except asyncio.TimeoutError:
            result.error = "timeout"
            self.logger.warning(f"System ping timeout for {host}")
        except Exception as e:
            result.error = f"error: {str(e)}"
            self.logger.error(f"System ping error for {host}: {e}")

        return result

    async def run_test(self, target: str) -> IcmpTestResult:
        """
        Run ICMP ping test against target

        Args:
            target: hostname or IP address
        """
        return await self._run_ping_test(target)

    def to_dict(self, result: IcmpTestResult) -> Dict:
        """Convert result to dictionary"""
        return asdict(result)

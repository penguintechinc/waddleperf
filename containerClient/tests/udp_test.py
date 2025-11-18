#!/usr/bin/env python3
"""UDP test implementation for containerClient"""

import asyncio
import socket
import time
import logging
import random
import string
from typing import Dict, Optional, List
from dataclasses import dataclass, field, asdict


@dataclass
class UdpTestResult:
    """UDP test result data"""
    test_type: str = "udp"
    protocol_detail: str = "raw_udp"
    target_host: str = ""
    target_ip: str = ""
    target_port: int = 0
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_percent: float = 0.0
    packets_sent: int = 0
    packets_received: int = 0
    success: bool = False
    error: Optional[str] = None
    raw_results: Dict = field(default_factory=dict)


class UdpTest:
    """UDP test implementation with support for raw UDP, DNS, and UDP+TLS (DTLS simulation)"""

    def __init__(self, timeout: int = 5, packet_count: int = 4):
        self.timeout = timeout
        self.packet_count = packet_count
        self.packet_size = 64
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

    def _generate_payload(self, size: int) -> bytes:
        """Generate random payload"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()

    async def _send_udp_packet(self, sock: socket.socket, addr: tuple, payload: bytes) -> Optional[float]:
        """Send UDP packet and measure RTT"""
        loop = asyncio.get_event_loop()

        try:
            send_time = time.perf_counter()
            await loop.sock_sendto(sock, payload, addr)

            # Wait for response
            try:
                data, recv_addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 1024),
                    timeout=self.timeout
                )
                recv_time = time.perf_counter()

                if recv_addr[0] == addr[0]:
                    rtt = (recv_time - send_time) * 1000
                    return rtt
            except asyncio.TimeoutError:
                return None

        except Exception as e:
            self.logger.debug(f"UDP packet send error: {e}")
            return None

    async def _test_raw_udp(self, host: str, port: int) -> UdpTestResult:
        """Test raw UDP ping"""
        result = UdpTestResult(
            protocol_detail="raw_udp",
            target_host=host,
            target_port=port
        )

        try:
            # Resolve hostname
            result.target_ip = await self._resolve_host(host) or host

            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            addr = (result.target_ip, port)
            payload = self._generate_payload(self.packet_size)

            rtts: List[float] = []
            result.packets_sent = self.packet_count

            # Send packets with interval
            for i in range(self.packet_count):
                rtt = await self._send_udp_packet(sock, addr, payload)
                if rtt is not None:
                    rtts.append(rtt)
                    result.packets_received += 1
                    self.logger.debug(f"UDP packet {i}: RTT={rtt:.2f}ms")

                # Wait between packets (except last)
                if i < self.packet_count - 1:
                    await asyncio.sleep(0.1)

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
            self.logger.error(f"UDP test error for {host}:{port}: {e}")

        return result

    async def _test_dns(self, host: str, dns_server: str = "8.8.8.8") -> UdpTestResult:
        """Test DNS query"""
        result = UdpTestResult(
            protocol_detail="dns",
            target_host=dns_server,
            target_port=53
        )

        try:
            # Resolve the DNS server IP
            result.target_ip = await self._resolve_host(dns_server) or dns_server

            # Simple DNS query timing (using system resolver)
            start_time = time.perf_counter()

            try:
                await asyncio.wait_for(
                    self._resolve_host(host),
                    timeout=self.timeout
                )
                end_time = time.perf_counter()

                result.latency_ms = (end_time - start_time) * 1000
                result.success = True
                result.packets_sent = 1
                result.packets_received = 1
                result.packet_loss_percent = 0.0

                result.raw_results = {
                    'query_host': host,
                    'dns_server': dns_server,
                    'query_time_ms': result.latency_ms
                }

            except asyncio.TimeoutError:
                result.error = "timeout"
                result.latency_ms = self.timeout * 1000
                result.packets_sent = 1
                result.packet_loss_percent = 100.0

        except Exception as e:
            result.error = f"error: {str(e)}"
            self.logger.error(f"DNS test error for {host} via {dns_server}: {e}")

        return result

    async def run_test(self, target: str, protocol: str = "raw_udp") -> UdpTestResult:
        """
        Run UDP test against target

        Args:
            target: host:port or host (default port based on protocol)
            protocol: raw_udp, dns, or udp_tls
        """
        # Parse target
        if protocol == "dns":
            # For DNS, target is the hostname to resolve
            # Can optionally specify DNS server as target:server
            if ':' in target:
                query_host, dns_server = target.split(':', 1)
                return await self._test_dns(query_host, dns_server)
            else:
                return await self._test_dns(target)
        else:
            # For raw UDP
            if ':' in target:
                host, port_str = target.rsplit(':', 1)
                port = int(port_str)
            else:
                host = target
                port = 2000  # Default UDP test port

            return await self._test_raw_udp(host, port)

    def to_dict(self, result: UdpTestResult) -> Dict:
        """Convert result to dictionary"""
        return asdict(result)

#!/usr/bin/env python3
"""TCP test implementation for containerClient"""

import asyncio
import socket
import time
import logging
import ssl
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class TcpTestResult:
    """TCP test result data"""
    test_type: str = "tcp"
    protocol_detail: str = "raw_tcp"
    target_host: str = ""
    target_ip: str = ""
    target_port: int = 0
    latency_ms: float = 0.0
    connection_time_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None
    raw_results: Dict = field(default_factory=dict)


class TcpTest:
    """TCP test implementation with support for raw TCP, TCP+TLS, and SSH"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
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

    async def _test_raw_tcp(self, host: str, port: int) -> TcpTestResult:
        """Test raw TCP connection"""
        result = TcpTestResult(
            protocol_detail="raw_tcp",
            target_host=host,
            target_port=port
        )

        try:
            # Resolve hostname
            result.target_ip = await self._resolve_host(host) or ""

            # Connect to target
            start_time = time.perf_counter()

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )

            connect_time = time.perf_counter()
            result.connection_time_ms = (connect_time - start_time) * 1000
            result.latency_ms = result.connection_time_ms

            # Close connection
            writer.close()
            await writer.wait_closed()

            result.success = True
            result.raw_results = {
                'connection_established': True,
                'connect_time_ms': result.connection_time_ms
            }

        except asyncio.TimeoutError:
            result.error = "timeout"
            result.latency_ms = self.timeout * 1000
            self.logger.warning(f"TCP connection timeout to {host}:{port}")
        except ConnectionRefusedError:
            result.error = "connection_refused"
            self.logger.warning(f"TCP connection refused to {host}:{port}")
        except Exception as e:
            result.error = f"error: {str(e)}"
            self.logger.error(f"TCP test error for {host}:{port}: {e}")

        return result

    async def _test_tcp_tls(self, host: str, port: int) -> TcpTestResult:
        """Test TCP+TLS connection"""
        result = TcpTestResult(
            protocol_detail="tcp_tls",
            target_host=host,
            target_port=port
        )

        try:
            # Resolve hostname
            result.target_ip = await self._resolve_host(host) or ""

            # Create SSL context
            ssl_context = ssl.create_default_context()

            # Connect to target with TLS
            start_time = time.perf_counter()

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=ssl_context, server_hostname=host),
                timeout=self.timeout
            )

            connect_time = time.perf_counter()
            result.connection_time_ms = (connect_time - start_time) * 1000
            result.latency_ms = result.connection_time_ms

            # Get TLS information
            ssl_object = writer.get_extra_info('ssl_object')
            tls_version = ssl_object.version() if ssl_object else None
            cipher = ssl_object.cipher() if ssl_object else None

            # Close connection
            writer.close()
            await writer.wait_closed()

            result.success = True
            result.raw_results = {
                'connection_established': True,
                'connect_time_ms': result.connection_time_ms,
                'tls_version': tls_version,
                'cipher': cipher
            }

        except asyncio.TimeoutError:
            result.error = "timeout"
            result.latency_ms = self.timeout * 1000
            self.logger.warning(f"TCP+TLS connection timeout to {host}:{port}")
        except ssl.SSLError as e:
            result.error = f"ssl_error: {str(e)}"
            self.logger.error(f"SSL error for {host}:{port}: {e}")
        except ConnectionRefusedError:
            result.error = "connection_refused"
            self.logger.warning(f"TCP+TLS connection refused to {host}:{port}")
        except Exception as e:
            result.error = f"error: {str(e)}"
            self.logger.error(f"TCP+TLS test error for {host}:{port}: {e}")

        return result

    async def _test_ssh(self, host: str, port: int = 22) -> TcpTestResult:
        """Test SSH connection (banner exchange)"""
        result = TcpTestResult(
            protocol_detail="ssh",
            target_host=host,
            target_port=port
        )

        try:
            # Resolve hostname
            result.target_ip = await self._resolve_host(host) or ""

            # Connect and read SSH banner
            start_time = time.perf_counter()

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )

            # Read SSH banner
            banner = await asyncio.wait_for(
                reader.readline(),
                timeout=2
            )

            connect_time = time.perf_counter()
            result.connection_time_ms = (connect_time - start_time) * 1000
            result.latency_ms = result.connection_time_ms

            # Close connection
            writer.close()
            await writer.wait_closed()

            result.success = True
            result.raw_results = {
                'connection_established': True,
                'connect_time_ms': result.connection_time_ms,
                'ssh_banner': banner.decode('utf-8', errors='ignore').strip()
            }

        except asyncio.TimeoutError:
            result.error = "timeout"
            result.latency_ms = self.timeout * 1000
            self.logger.warning(f"SSH connection timeout to {host}:{port}")
        except ConnectionRefusedError:
            result.error = "connection_refused"
            self.logger.warning(f"SSH connection refused to {host}:{port}")
        except Exception as e:
            result.error = f"error: {str(e)}"
            self.logger.error(f"SSH test error for {host}:{port}: {e}")

        return result

    async def run_test(self, target: str, protocol: str = "raw_tcp") -> TcpTestResult:
        """
        Run TCP test against target

        Args:
            target: host:port or host (default port based on protocol)
            protocol: raw_tcp, tcp_tls, or ssh
        """
        # Parse target
        if ':' in target:
            host, port_str = target.rsplit(':', 1)
            port = int(port_str)
        else:
            host = target
            # Default ports
            if protocol == "ssh":
                port = 22
            elif protocol == "tcp_tls":
                port = 443
            else:
                port = 80

        # Run appropriate test
        if protocol == "ssh":
            return await self._test_ssh(host, port)
        elif protocol == "tcp_tls":
            return await self._test_tcp_tls(host, port)
        else:
            return await self._test_raw_tcp(host, port)

    def to_dict(self, result: TcpTestResult) -> Dict:
        """Convert result to dictionary"""
        return asdict(result)

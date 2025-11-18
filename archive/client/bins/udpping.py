#!/usr/bin/env python3
# Original source inspiration https://github.com/wangyu-/UDPping/blob/master/udpping.py
# Cleaned up using CoPilot and migrated to Python 3.11

import sys
import time
import string
import random
import signal
import os
import getopt
import json
import socket
import logging
import base64

class UDPPing:
    def __init__(self, DSTHOST=None, PORT=None):
        self.INTERVAL = 1000  # unit ms
        self.LEN = 64
        if DSTHOST is None:
            self.DSTHOST = "127.0.0.1"
        else:
            self.DSTHOST = DSTHOST  
        if PORT is None:
            self.PORT = 2000
        else:
            self.PORT = PORT
        self.PING_COUNT = 4  # Default count set to 4
        self.OUTPUT_FILE = "udppingresults.json"  # Default output file
        self.TTL = 64  # Default TTL value
        self.LOG_LEVEL = logging.INFO  # Default logging level
        self.TOKEN = None  # Default token value

        self.count = 0
        self.count_of_received = 0
        self.rtt_sum = 0.0
        self.rtt_min = float('inf')
        self.rtt_max = 0.0

    def signal_handler(self, signal, frame):
        if self.count != 0 and self.count_of_received != 0:
            logging.info('--- ping statistics ---')
        if self.count != 0:
            logging.info(f'{self.count} packets transmitted, {self.count_of_received} received, {(self.count - self.count_of_received) * 100.0 / self.count:.2f}% packet loss')
        if self.count_of_received != 0:
            logging.info(f'rtt min/avg/max = {self.rtt_min:.2f}/{self.rtt_sum / self.count_of_received:.2f}/{self.rtt_max:.2f} ms')
        self.write_statistics_to_json()
        os._exit(0)

    def write_statistics_to_json(self):
        statistics = {
            'packets_transmitted': self.count,
            'packets_received': self.count_of_received,
            'packet_loss': (self.count - self.count_of_received) * 100.0 / self.count if self.count != 0 else 0,
            'rtt_min': self.rtt_min if self.count_of_received != 0 else None,
            'rtt_avg': self.rtt_sum / self.count_of_received if self.count_of_received != 0 else None,
            'rtt_max': self.rtt_max if self.count_of_received != 0 else None
        }
        with open(self.OUTPUT_FILE, 'w') as json_file:
            json.dump(statistics, json_file, indent=4)

    def random_string(self, length):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    def parse_options(self, options):
        for option in options.split(';'):
            key, value = option.split('=')
            if key == 'LEN':
                self.LEN = int(value)
            elif key == 'INTERVAL':
                self.INTERVAL = int(value)

    def run(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "a:c:o:p:f:t:l:k:h", ["address=", "count=", "options=", "port=", "file=", "ttl=", "loglevel=", "token=", "help"])
        except getopt.GetoptError as err:
            logging.error(str(err))
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-a", "--address"):
                self.DSTHOST = arg
            elif opt in ("-c", "--count"):
                self.PING_COUNT = int(arg)
            elif opt in ("-o", "--options"):
                self.parse_options(arg)
            elif opt in ("-p", "--port"):
                self.PORT = int(arg)
            elif opt in ("-f", "--file"):
                self.OUTPUT_FILE = arg
            elif opt in ("-t", "--ttl"):
                self.TTL = int(arg)
            elif opt in ("-l", "--loglevel"):
                self.LOG_LEVEL = getattr(logging, arg.upper(), logging.INFO)
            elif opt in ("-k", "--token"):
                self.TOKEN = arg
            elif opt in ("-h", "--help"):
                print("Usage: udpping.py -a <address or hostname> -c <count> -p <port> -f <output_file> -l <loglevel> -k <token>")
                sys.exit()
        if not self.DSTHOST or not self.PORT:
            print("Usage: udpping.py -a <address or hostname> -c <count> -p <port> -f <output_file> -l <loglevel> -k <token>")
            sys.exit(2)

        if self.LEN < 5:
            logging.error("LEN must be >=5")
            exit()
        if self.INTERVAL < 50:
            logging.error("INTERVAL must be >=50")
            exit()

        logging.basicConfig(level=self.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

        signal.signal(signal.SIGINT, self.signal_handler)

        logging.info(f"UDPping {self.DSTHOST} via port {self.PORT} with {self.LEN} bytes of payload")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.INTERVAL / 1000.0)
        sock.setsockopt(socket.SOL_IP, socket.IP_TTL, self.TTL)

        while self.PING_COUNT is None or self.count < self.PING_COUNT:
            payload = self.random_string(self.LEN).encode()
            if self.TOKEN:
                encoded_token = base64.b64encode(self.TOKEN.encode()).decode()
                payload = f"{encoded_token}:{payload.decode()}".encode()
            time_of_send = time.perf_counter()
            sock.sendto(payload, (self.DSTHOST, self.PORT))
            deadline = time_of_send + self.INTERVAL / 1000.0
            received = 0
            rtt = 0.0

            try:
                while True:
                    timeout = deadline - time.perf_counter()
                    if timeout < 0:
                        break
                    sock.settimeout(timeout)
                    response, addr = sock.recvfrom(1024)
                    if addr[0] == self.DSTHOST and addr[1] == self.PORT:
                        recv_time = time.perf_counter()
                        rtt = (recv_time - time_of_send) * 1000
                        logging.info(f"Reply from {self.DSTHOST} seq={self.count} time={rtt:.2f} ms")
                        received = 1
                        break
            except socket.timeout:
                pass

            self.count += 1
            if received == 1:
                self.count_of_received += 1
                self.rtt_sum += rtt
                self.rtt_max = max(self.rtt_max, rtt)
                self.rtt_min = min(self.rtt_min, rtt)
            else:
                logging.warning("Request timed out")

            time_remaining = deadline - time.perf_counter()
            if time_remaining > 0:
                time.sleep(time_remaining)

        self.signal_handler(None, None)

if __name__ == "__main__":
    UDPPing().run()

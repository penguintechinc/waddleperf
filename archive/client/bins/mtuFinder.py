#! /usr/bin/env python3

import subprocess
import platform
import json
import logging
import sys

class MTUFinder:
    def __init__(self, host):
        self.host = host
        self.results = []
        logging.basicConfig(level=logging.INFO)

    def run(self) -> dict:
        min_size, max_size = self.test_mtu(500, 2000, 100)
        if min_size == max_size:
            logging.critical("Unable to ping host %s on first try! Check the host and try again." % self.host)
            return None
        min_size, max_size = self.test_mtu(min_size, max_size, 20)
        logging.info("Range Found: %d - %d", min_size, max_size)
        min_size, max_size = self.test_mtu(min_size, max_size, 5)
        logging.info("Range Found: %d - %d", min_size, max_size)
        min_size, max_size = self.test_mtu(min_size, max_size, 1)
        logging.info("Range Found: %d - %d", min_size, max_size)
        return {"maxMTU": max_size}

    def test_mtu(self, min_size: int = 1000, max_size: int = 1900, step_size: int = 1) -> tuple:
        if min_size < 1 or max_size < 1 or step_size < 1 or min_size > 2000 or max_size > 2000 or step_size > 2000:
            logging.error("Invalid parameters! Check the parameters and try again.")
            return None
        for c in range(min_size, max_size, step_size):
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["ping", "-n", "1", "-f", "-l", str(c), self.host],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                result = subprocess.run(
                    ["ping", "-c", "1", "-M", "do", "-s", str(c), self.host],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            self.results.append({
                "size": c,
                "success": result.returncode == 0,
                "output": result.stdout.decode()
            })
            if result.returncode != 0 and c == min_size:
                logging.debug("Unable to ping host %s ! Check the host and try again." % self.host)
                return c, c
            if result.returncode != 0:
                return c - step_size, c

if __name__ == "__main__":
    host = "8.8.8.8"  # Example host, you can change it to the desired host
    mtu_finder = MTUFinder(host)
    max_mtu = mtu_finder.run()
    print(json.dumps(mtu_finder.results, indent=4))
    if max_mtu is None:
        sys.exit(1)
    print(f"The maximum MTU size for {host} is {max_mtu['maxMTU']} bytes")
    
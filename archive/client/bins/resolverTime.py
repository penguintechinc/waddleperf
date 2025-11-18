#! /usr/bin/env python3
import sys
import getopt
import socket
import time
import json
import statistics
import logging
import os
import dns
import dns.resolver

class resolverTime:
    domain = 'google.com'
    count = 3
    record_type = 'A'
    dns_server = None
    output_file = None
    results = {}

    @classmethod
    def resolve_dns(cls):
        times = []
        resolve = None
        for _ in range(cls.count):
            start_time = time.perf_counter()
            try:
                if cls.dns_server:
                    resolve = dns.resolver.Resolver()
                    resolve.nameservers = [cls.dns_server]
                    try:
                        resolve.resolve(cls.domain, cls.record_type)
                    except dns.resolver.NXDOMAIN:
                        print(f"Error: Domain '{cls.domain}' not found.")
                        return []
                    except dns.resolver.Timeout:
                        print(f"Error: Timeout while querying '{cls.dns_server}'.")
                        return []
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")
                        return []
                else:
                    socket.gethostbyname(cls.domain)
                end_time = time.perf_counter()
                difference = end_time - start_time
                times.append("%s" % difference)
            except Exception as e:
                print(f"An error occurred: {e} for domain {cls.domain} recordType {cls.record_type} on line {e.__traceback__.tb_lineno}")
                times.append(None)
        return times

    @classmethod
    def run(cls):
        if not cls.domain:
            logging.error('Domain name is required')
            sys.exit(2)

        times = cls.resolve_dns()
        # Remove all nones from the list
        logging.debug(times)
        times = [time for time in times if time is not None]
        if len(times) == 0:
            logging.error('No successful DNS resolutions')
            sys.exit(2)
        cls.results = {
            "domain": cls.domain,
            "count": cls.count,
            "successful_count": len(times),
            "record_type": cls.record_type,
            "times": times,
            "min_time": min(times),
            "mean_time": statistics.mean([float(time) for time in times]),
            "max_time": max(times)
        }

        result_json = json.dumps(cls.results, indent=4)
        print(result_json)

        if cls.output_file:
            with open(cls.output_file, 'w') as f:
                f.write(result_json)
        return result_json
def main(argv):
    try:
        opts = getopt.getopt(argv, "hd:c:t:s:o:", ["domain=", "count=", "type=", "server=", "output="])[0]
    except getopt.GetoptError:
        logging.error('resolverTime.py -d <domain> -c <count> -t <record_type> -s <dns_server> -o <output_file>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logging.info('resolverTime.py -d <domain> -c <count> -t <record_type> -s <dns_server> -o <output_file>')
            sys.exit()
        elif opt in ("-d", "--domain"):
            resolverTime.domain = arg
        elif opt in ("-c", "--count"):
            resolverTime.count = int(arg)
        elif opt in ("-t", "--type"):
            resolverTime.record_type = arg
        elif opt in ("-s", "--server"):
            resolverTime.dns_server = arg
        elif opt in ("-o", "--output"):
            resolverTime.output_file = arg

    resolverTime.run()

if __name__ == "__main__":
    log_file = '/var/log/resolverTime.log' if os.name != 'nt' else 'resolverTime.log'
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ])
    main(sys.argv[1:])

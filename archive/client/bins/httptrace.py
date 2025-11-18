#!/usr/bin/env python3
import subprocess
import json
import sys
import getopt
import statistics
import logging
import os

class HttpTrace:
    def __init__(self, url, tries=1, output_file=None):
        self.url = url
        self.tries = tries
        self.output_file = output_file
        self.results = {}

    def measure_http_load_time(self):
        try:
            result = subprocess.run(
                ['curl', '-w', '@-', '-o', '/dev/null', '-s', self.url],
                input='''{
                    "url_effective": "%{url_effective}",
                    "http_code": %{http_code},
                    "time_namelookup": %{time_namelookup},
                    "time_connect": %{time_connect},
                    "time_appconnect": %{time_appconnect},
                    "time_pretransfer": %{time_pretransfer},
                    "time_redirect": %{time_redirect},
                    "time_starttransfer": %{time_starttransfer},
                    "time_total": %{time_total}
                }''',
                text=True,
                capture_output=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return None

    def run(self):
        self.results["details"] = []
        for c in range(self.tries):
            load_time_data = self.measure_http_load_time()
            if load_time_data:
                self.results["details"].append(load_time_data)

        if self.results:
            self.results["summary"] = {
                "min_time": min(result['time_total'] for result in self.results["details"]),
                "mean_time": statistics.mean(result['time_total'] for result in self.results["details"]),
                "max_time": max(result['time_total'] for result in self.results["details"]),
                "mean_time": statistics.mean(result['time_total'] for result in self.results["details"]),
                "all_times": [result['time_total'] for result in self.results["details"]],
            }
            summary_json = json.dumps(self.results, indent=4)
            logging.info(summary_json)
            if self.output_file:
                with open(self.output_file, 'w') as f:
                    f.write(summary_json)

def main(argv):
    url = ''
    tries = 1
    output_file = None

    try:
        opts, args = getopt.getopt(argv, "hu:t:o:", ["url=", "tries=", "output="])
    except getopt.GetoptError:
        logging.error("Usage: python httptrace.py -u <URL> -t <TRIES> -o <OUTPUT_FILE>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print("Usage: python httptrace.py -u <URL> -t <TRIES> -o <OUTPUT_FILE>")
            sys.exit()
        elif opt in ("-u", "--url"):
            url = arg
        elif opt in ("-t", "--tries"):
            tries = int(arg)
        elif opt in ("-o", "--output"):
            output_file = arg

    if not url:
        logging.error("URL is required. Usage: python httptrace.py -u <URL> -t <TRIES> -o <OUTPUT_FILE>")
        sys.exit(2)

    http_trace = HttpTrace(url, tries, output_file)
    http_trace.run()

if __name__ == "__main__":
    log_file = "/var/log/httptrace.log" if os.name != 'nt' else "httptrace.log"
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
    main(sys.argv[1:])

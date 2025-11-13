#! /usr/bin/env python3
import paramiko
import time
import statistics
import json
import getopt
import sys
from getpass import getpass
from datetime import datetime

class SSHPing:
    def __init__(self, hostname, port=22, username=None, password=None, key_filename=None, num_pings=10, file_size_mb=1):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.num_pings = num_pings
        self.file_size_mb = file_size_mb

    def run(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.key_filename:
                client.connect(self.hostname, port=self.port, username=self.username, key_filename=self.key_filename)
            else:
                client.connect(self.hostname, port=self.port, username=self.username, password=self.password)
            
            latencies = []
            start_time = datetime.now().isoformat()
            
            for i in range(self.num_pings):
                ping_start_time = time.time()
                stdin, stdout, stderr = client.exec_command('echo ping')
                stdout.channel.recv_exit_status()  # Wait for command to complete
                ping_end_time = time.time()
                
                latency = (ping_end_time - ping_start_time) * 1000  # Convert to milliseconds
                latencies.append(latency)
            
            min_latency = min(latencies) * 1000 # Convert to milliseconds
            avg_latency = statistics.mean(latencies) * 1000 # Convert to milliseconds
            max_latency = max(latencies) * 1000 # Convert to milliseconds
            upload_time = self.upload_test() * 1000 # Convert to milliseconds
            results = {
                "hostname": self.hostname,
                "port": self.port,
                "username": self.username,
                "start_time": start_time,
                "pingLatency": {
                    "num_pings": self.num_pings,
                    "stats": { # All latencies in milliseconds
                        "min": min_latency,
                        "avg": avg_latency,
                        "max": max_latency
                    },
                    "probes": latencies
                },
                "fileLatency": {
                    "fileSizeMB": self.file_size_mb,
                    "upload_time": upload_time
                }
            }
            print("All results in Milliseconds:")
            print(json.dumps(results, indent=4))
            
            with open('ssh-results.json', 'w') as f:
                json.dump(results, f, indent=4)
            
        except Exception as e:
            print(f"Failed to connect or execute command: {e}")
        finally:
            client.close()

    @staticmethod
    def usage():
        print("Usage: sshping.py -h <hostname> -P <port> -u <username> [-k <key_filename>] [-n <num_pings>] [-s <file_size_mb>]")
        
    def upload_test(self):
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                if self.key_filename:
                    client.connect(self.hostname, port=self.port, username=self.username, key_filename=self.key_filename)
                else:
                    client.connect(self.hostname, port=self.port, username=self.username, password=self.password)
                
                sftp = client.open_sftp()
                random_data = bytearray(1024 * 1024 * self.file_size_mb)  # File size in MB
                start_time = time.time()
                
                with sftp.file('upload_test_file', 'wb') as f:
                    f.write(random_data)
                
                end_time = time.time()
                upload_time = end_time - start_time
                sftp.remove('upload_test_file')  # Clean up the uploaded file
                sftp.close()
                
                return upload_time
            
            except Exception as e:
                print(f"Failed to connect or upload file: {e}")
                return None
            finally:
                client.close()

if __name__ == "__main__":
    hostname = None
    port = 22
    username = None
    key_filename = None
    num_pings = 3
    file_size_mb = 1

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:P:u:k:n:s:", ["hostname=", "port=", "username=", "key=", "num_pings=", "file_size_mb="])
    except getopt.GetoptError as err:
        print(err)
        SSHPing.usage()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--hostname"):
            hostname = arg
        elif opt in ("-P", "--port"):
            port = int(arg)
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-k", "--key"):
            key_filename = arg
        elif opt in ("-n", "--num_pings"):
            num_pings = int(arg)
        elif opt in ("-s", "--file_size_mb"):
            if int(arg) < 1 or int(arg) > 100:
                print("File size must be at least 1 and no larger then 100")
                sys.exit(2)
            file_size_mb = int(arg)
    
    if not hostname or not username:
        SSHPing.usage()
        sys.exit(2)
    
    password = None
    if not key_filename:
        password = getpass(prompt='Password: ', stream=None)
    
    ssh_ping = SSHPing(hostname, port, username, password, key_filename, num_pings, file_size_mb)
    ssh_ping.run()
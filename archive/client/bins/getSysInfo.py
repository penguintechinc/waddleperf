#! /usr/bin/env python3
import json
import platform
import psutil
import subprocess
import sys
import getopt

class SystemInfo:
    def __init__(self, infoTypes: list = ['all']):
        self.system_info = {}
        self.info_types = infoTypes

    def get_wifi_profiles(self) -> tuple:
        wifi_profiles = []
        current_ssid = None

        if platform.system() == "Windows":
            try:
                profiles_data = subprocess.check_output("netsh wlan show profiles", shell=True).decode()
                profiles = [line.split(":")[1].strip() for line in profiles_data.split("\n") if "All User Profile" in line]
                for profile in profiles:
                    profile_info = subprocess.check_output(f"netsh wlan show profile name=\"{profile}\" key=clear", shell=True).decode()
                    ssid = profile
                    key_content = None
                    for line in profile_info.split("\n"):
                        if "Key Content" in line:
                            key_content = line.split(":")[1].strip()
                    wifi_profiles.append({"ssid": ssid, "key_content": key_content})
                
                current_ssid_data = subprocess.check_output("netsh wlan show interfaces", shell=True).decode()
                for line in current_ssid_data.split("\n"):
                    if "SSID" in line:
                        current_ssid = line.split(":")[1].strip()
                        break
            except subprocess.CalledProcessError:
                pass

        elif platform.system() == "Linux":
            try:
                profiles_data = subprocess.check_output("nmcli -t -f NAME connection show", shell=True).decode()
                profiles = profiles_data.split("\n")
                for profile in profiles:
                    if profile:
                        profile_info = subprocess.check_output(f"nmcli -s -g 802-11-wireless-security.psk connection show \"{profile}\"", shell=True).decode().strip()
                        wifi_profiles.append({"ssid": profile, "key_content": profile_info})
                
                current_ssid_data = subprocess.check_output("nmcli -t -f ACTIVE,SSID dev wifi", shell=True).decode()
                for line in current_ssid_data.split("\n"):
                    if line.startswith("yes:"):
                        current_ssid = line.split(":")[1].strip()
                        break
            except subprocess.CalledProcessError:
                pass

        elif platform.system() == "Darwin":
            try:
                profiles_data = subprocess.check_output("/usr/sbin/networksetup -listpreferredwirelessnetworks en0", shell=True).decode()
                profiles = [line.strip() for line in profiles_data.split("\n")[1:]]
                for profile in profiles:
                    wifi_profiles.append({"ssid": profile, "key_content": None})
                
                current_ssid_data = subprocess.check_output("/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I", shell=True).decode()
                for line in current_ssid_data.split("\n"):
                    if " SSID" in line:
                        current_ssid = line.split(":")[1].strip()
                        break
            except subprocess.CalledProcessError:
                pass

        return wifi_profiles, current_ssid

    def run(self) -> dict:
        
        if 'os' in self.info_types or 'all' in self.info_types:
            self.system_info['os_family'] = platform.system()
            self.system_info['os_version'] = platform.version()

        if 'cpu' in self.info_types or 'all' in self.info_types:
            cpu_info = {}
            cpu_info['cpu_usage'] = psutil.cpu_percent(interval=1)
            cpu_info['cpu_count'] = psutil.cpu_count(logical=True)
            cpu_info['cpu_physical_cores'] = psutil.cpu_count(logical=False)
            cpu_info['cpu_freq'] = psutil.cpu_freq()._asdict()
            cpu_info['cpu_architecture'] = platform.machine()
            self.system_info['cpu_info'] = cpu_info

        if 'memory' in self.info_types or 'all' in self.info_types:
            memory_info = {}
            virtual_mem = psutil.virtual_memory()
            memory_info['total_memory'] = virtual_mem.total
            memory_info['available_memory'] = virtual_mem.available
            memory_info['used_memory'] = virtual_mem.used
            memory_info['memory_usage'] = virtual_mem.percent
            self.system_info['memory_info'] = memory_info

        if 'disk' in self.info_types or 'all' in self.info_types:
            disk_info = {}
            disk_usage = psutil.disk_usage('/')
            disk_info['total_disk'] = disk_usage.total
            disk_info['used_disk'] = disk_usage.used
            disk_info['free_disk'] = disk_usage.free
            disk_info['disk_usage'] = disk_usage.percent

            disk_info['disk_models'] = []
            for disk in psutil.disk_partitions():
                try:
                    disk_info['disk_models'].append({
                        'device': disk.device,
                        'mountpoint': disk.mountpoint,
                        'fstype': disk.fstype,
                        'opts': disk.opts
                    })
                except PermissionError:
                    continue
            self.system_info['disk_info'] = disk_info

        if 'process' in self.info_types or 'all' in self.info_types:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'create_time', 'memory_info', 'cpu_times']):
                try:
                    proc_info = proc.info
                    proc_info['memory_info'] = proc.memory_info()._asdict()
                    proc_info['cpu_times'] = proc.cpu_times()._asdict()
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self.system_info['running_processes'] = processes

        if 'network' in self.info_types or 'all' in self.info_types:
            net_info = {}
            net_info['interfaces'] = []
            for interface, addrs in psutil.net_if_addrs().items():
                iface_info = {'name': interface, 'addresses': []}
                for addr in addrs:
                    addr_info = {
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    }
                    iface_info['addresses'].append(addr_info)
                net_info['interfaces'].append(iface_info)

            net_info['stats'] = psutil.net_if_stats()
            self.system_info['network_info'] = net_info

        if 'wifi' in self.info_types or 'all' in self.info_types:
            wifi_profiles, current_ssid = self.get_wifi_profiles()
            self.system_info['wifi_profiles'] = wifi_profiles
            self.system_info['current_ssid'] = current_ssid

        return self.system_info

    def save_system_info(self, filename=None):
        system_info = self.run()
        if filename:
            with open(filename, 'w') as json_file:
                json.dump(system_info, json_file, indent=4)
        print(json.dumps(system_info, indent=4))

def main(argv):
    output_file = None
    info_types = []
    try:
        opts, args = getopt.getopt(argv, "ho:", ["output=", "os", "cpu", "memory", "disk", "process", "network", "wifi"])
    except getopt.GetoptError:
        print('Usage: getSysInfo.py -o <outputfile> [--os] [--cpu] [--memory] [--disk] [--process] [--network] [--wifi]')
        print(" If you do not specify any options, all system information will be collected.")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('Usage: getSysInfo.py -o <outputfile> [--os] [--cpu] [--memory] [--disk] [--process] [--network] [--wifi]')
            sys.exit()
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt == "--os":
            info_types.append("os")
        elif opt == "--cpu":
            info_types.append("cpu")
        elif opt == "--memory":
            info_types.append("memory")
        elif opt == "--disk":
            info_types.append("disk")
        elif opt == "--process":
            info_types.append("process")
        elif opt == "--network":
            info_types.append("network")
        elif opt == "--wifi":
            info_types.append("wifi")

    if not info_types:
        info_types = ['all']

    sys_info = SystemInfo(infoTypes=info_types)
    sys_info.save_system_info(output_file)

if __name__ == "__main__":
    main(sys.argv[1:])

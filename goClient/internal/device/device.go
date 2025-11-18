package device

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"runtime"
	"strings"
)

type DeviceInfo struct {
	Serial     string `json:"serial"`
	Hostname   string `json:"hostname"`
	OS         string `json:"os"`
	OSVersion  string `json:"os_version"`
	Arch       string `json:"arch"`
	IPAddress  string `json:"ip_address"`
	MACAddress string `json:"mac_address"`
	CPUCount   int    `json:"cpu_count"`
	GoVersion  string `json:"go_version"`
}

func GetDeviceInfo(configSerial, configHostname string) (*DeviceInfo, error) {
	info := &DeviceInfo{
		OS:        runtime.GOOS,
		Arch:      runtime.GOARCH,
		CPUCount:  runtime.NumCPU(),
		GoVersion: runtime.Version(),
	}

	// Get hostname
	if configHostname == "auto" || configHostname == "" {
		hostname, err := os.Hostname()
		if err != nil {
			hostname = "unknown"
		}
		info.Hostname = hostname
	} else {
		info.Hostname = configHostname
	}

	// Get OS version
	info.OSVersion = getOSVersion()

	// Get serial number
	if configSerial == "auto" || configSerial == "" {
		serial, err := getSerialNumber()
		if err != nil {
			// Fallback to hostname-based identifier
			serial = fmt.Sprintf("waddle-%s-%s", info.Hostname, info.Arch)
		}
		info.Serial = serial
	} else {
		info.Serial = configSerial
	}

	// Get primary IP address
	info.IPAddress = getPrimaryIPAddress()

	// Get primary MAC address
	info.MACAddress = getPrimaryMACAddress()

	return info, nil
}

func getOSVersion() string {
	switch runtime.GOOS {
	case "linux":
		return getLinuxVersion()
	case "darwin":
		return getMacOSVersion()
	case "windows":
		return getWindowsVersion()
	default:
		return "unknown"
	}
}

func getLinuxVersion() string {
	// Try reading /etc/os-release
	data, err := os.ReadFile("/etc/os-release")
	if err == nil {
		lines := strings.Split(string(data), "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "PRETTY_NAME=") {
				version := strings.TrimPrefix(line, "PRETTY_NAME=")
				version = strings.Trim(version, "\"")
				return version
			}
		}
	}

	// Fallback to uname
	cmd := exec.Command("uname", "-r")
	output, err := cmd.Output()
	if err == nil {
		return strings.TrimSpace(string(output))
	}

	return "Linux (unknown version)"
}

func getMacOSVersion() string {
	cmd := exec.Command("sw_vers", "-productVersion")
	output, err := cmd.Output()
	if err == nil {
		return fmt.Sprintf("macOS %s", strings.TrimSpace(string(output)))
	}

	return "macOS (unknown version)"
}

func getWindowsVersion() string {
	cmd := exec.Command("cmd", "/c", "ver")
	output, err := cmd.Output()
	if err == nil {
		return strings.TrimSpace(string(output))
	}

	return "Windows (unknown version)"
}

func getSerialNumber() (string, error) {
	switch runtime.GOOS {
	case "linux":
		return getLinuxSerial()
	case "darwin":
		return getMacOSSerial()
	case "windows":
		return getWindowsSerial()
	default:
		return "", fmt.Errorf("unsupported OS: %s", runtime.GOOS)
	}
}

func getLinuxSerial() (string, error) {
	// Try reading DMI information
	paths := []string{
		"/sys/class/dmi/id/product_serial",
		"/sys/class/dmi/id/product_uuid",
		"/sys/class/dmi/id/board_serial",
	}

	for _, path := range paths {
		data, err := os.ReadFile(path)
		if err == nil {
			serial := strings.TrimSpace(string(data))
			if serial != "" && serial != "0" && serial != "Not Specified" {
				return serial, nil
			}
		}
	}

	// Try dmidecode (requires root)
	cmd := exec.Command("dmidecode", "-s", "system-serial-number")
	output, err := cmd.Output()
	if err == nil {
		serial := strings.TrimSpace(string(output))
		if serial != "" && serial != "Not Specified" {
			return serial, nil
		}
	}

	// Try machine-id as fallback
	data, err := os.ReadFile("/etc/machine-id")
	if err == nil {
		return strings.TrimSpace(string(data)), nil
	}

	return "", fmt.Errorf("unable to determine serial number")
}

func getMacOSSerial() (string, error) {
	cmd := exec.Command("ioreg", "-l")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	// Search for IOPlatformSerialNumber
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "IOPlatformSerialNumber") {
			parts := strings.Split(line, "=")
			if len(parts) >= 2 {
				serial := strings.TrimSpace(parts[1])
				serial = strings.Trim(serial, "\" ")
				return serial, nil
			}
		}
	}

	// Alternative method
	cmd = exec.Command("system_profiler", "SPHardwareDataType")
	output, err = cmd.Output()
	if err != nil {
		return "", err
	}

	lines = strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "Serial Number") {
			parts := strings.Split(line, ":")
			if len(parts) >= 2 {
				serial := strings.TrimSpace(parts[1])
				return serial, nil
			}
		}
	}

	return "", fmt.Errorf("unable to determine serial number")
}

func getWindowsSerial() (string, error) {
	cmd := exec.Command("wmic", "bios", "get", "serialnumber")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	lines := strings.Split(string(output), "\n")
	if len(lines) >= 2 {
		serial := strings.TrimSpace(lines[1])
		if serial != "" {
			return serial, nil
		}
	}

	return "", fmt.Errorf("unable to determine serial number")
}

func getPrimaryIPAddress() string {
	interfaces, err := net.Interfaces()
	if err != nil {
		return "unknown"
	}

	for _, iface := range interfaces {
		// Skip down interfaces
		if iface.Flags&net.FlagUp == 0 {
			continue
		}

		// Skip loopback
		if iface.Flags&net.FlagLoopback != 0 {
			continue
		}

		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}

		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}

			if ip == nil || ip.IsLoopback() {
				continue
			}

			// Prefer IPv4
			if ip.To4() != nil {
				return ip.String()
			}
		}
	}

	return "unknown"
}

func getPrimaryMACAddress() string {
	interfaces, err := net.Interfaces()
	if err != nil {
		return "unknown"
	}

	for _, iface := range interfaces {
		// Skip down interfaces
		if iface.Flags&net.FlagUp == 0 {
			continue
		}

		// Skip loopback
		if iface.Flags&net.FlagLoopback != 0 {
			continue
		}

		// Skip interfaces without hardware address
		if len(iface.HardwareAddr) == 0 {
			continue
		}

		return iface.HardwareAddr.String()
	}

	return "unknown"
}

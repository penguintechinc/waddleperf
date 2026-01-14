package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Manager    ManagerConfig    `yaml:"manager"`
	TestServer TestServerConfig `yaml:"testServer"`
	Tests      TestsConfig      `yaml:"tests"`
	Schedule   ScheduleConfig   `yaml:"schedule"`
	Device     DeviceConfig     `yaml:"device"`
	Logging    LoggingConfig    `yaml:"logging"`
}

type ManagerConfig struct {
	URL               string `yaml:"url"`
	APIKey            string `yaml:"api_key"`
	AccessTokenPath   string `yaml:"access_token_path"`
	RefreshTokenPath  string `yaml:"refresh_token_path"`
}

type TestServerConfig struct {
	URL string `yaml:"url"`
}

type TestsConfig struct {
	HTTP HTTPTestsConfig `yaml:"http"`
	TCP  TCPTestsConfig  `yaml:"tcp"`
	UDP  UDPTestsConfig  `yaml:"udp"`
	ICMP ICMPTestsConfig `yaml:"icmp"`
}

type HTTPTestsConfig struct {
	Enabled  bool               `yaml:"enabled"`
	Targets  []string           `yaml:"targets"`
	Protocol string             `yaml:"protocol"` // http1, http2, http3, auto
	Timeout  int                `yaml:"timeout"`
	Advanced HTTPAdvancedConfig `yaml:"advanced,omitempty"`
}

type HTTPAdvancedConfig struct {
	Method            string `yaml:"method"`
	FollowRedirects   bool   `yaml:"follow_redirects"`
	VerifyTLS         bool   `yaml:"verify_tls"`
	MaxRedirects      int    `yaml:"max_redirects"`
	UserAgent         string `yaml:"user_agent"`
	MeasureTransfer   bool   `yaml:"measure_transfer"`
	MeasureDetailedMS bool   `yaml:"measure_detailed_ms"`
}

type TCPTestsConfig struct {
	Enabled  bool              `yaml:"enabled"`
	Targets  []TCPTargetConfig `yaml:"targets"`
	Timeout  int               `yaml:"timeout"`
	Advanced TCPAdvancedConfig `yaml:"advanced,omitempty"`
}

type TCPTargetConfig struct {
	Address  string `yaml:"address"`
	Protocol string `yaml:"protocol"` // raw, tls, ssh
}

type TCPAdvancedConfig struct {
	VerifyTLS      bool `yaml:"verify_tls"`
	KeepAlive      bool `yaml:"keep_alive"`
	RetryOnFailure bool `yaml:"retry_on_failure"`
	RetryAttempts  int  `yaml:"retry_attempts"`
}

type UDPTestsConfig struct {
	Enabled  bool              `yaml:"enabled"`
	Targets  []UDPTargetConfig `yaml:"targets"`
	Timeout  int               `yaml:"timeout"`
	Advanced UDPAdvancedConfig `yaml:"advanced,omitempty"`
}

type UDPTargetConfig struct {
	Address  string `yaml:"address"`
	Protocol string `yaml:"protocol"`        // raw, dns
	Query    string `yaml:"query,omitempty"` // For DNS
}

type UDPAdvancedConfig struct {
	RetryOnFailure bool `yaml:"retry_on_failure"`
	RetryAttempts  int  `yaml:"retry_attempts"`
}

type ICMPTestsConfig struct {
	Enabled  bool               `yaml:"enabled"`
	Targets  []string           `yaml:"targets"`
	Protocol string             `yaml:"protocol"` // ping, traceroute
	Count    int                `yaml:"count"`
	Timeout  int                `yaml:"timeout"`
	Advanced ICMPAdvancedConfig `yaml:"advanced,omitempty"`
}

type ICMPAdvancedConfig struct {
	PacketSize        int  `yaml:"packet_size"`
	DontFragment      bool `yaml:"dont_fragment"`
	MeasureJitter     bool `yaml:"measure_jitter"`
	TracerouteMaxHops int  `yaml:"traceroute_max_hops"`
}

type ScheduleConfig struct {
	IntervalSeconds int  `yaml:"interval_seconds"`
	Enabled         bool `yaml:"enabled"`
	RunOnStartup    bool `yaml:"run_on_startup"`
}

type DeviceConfig struct {
	Serial   string `yaml:"serial"`   // "auto" for auto-detect
	Hostname string `yaml:"hostname"` // "auto" for auto-detect
}

type LoggingConfig struct {
	Level    string `yaml:"level"` // debug, info, warn, error
	FilePath string `yaml:"file_path"`
	Console  bool   `yaml:"console"`
}

func LoadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	// Validate and set defaults
	if err := config.Validate(); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	config.SetDefaults()

	return &config, nil
}

func (c *Config) Validate() error {
	if c.Manager.URL == "" {
		return fmt.Errorf("manager.url is required")
	}
	if c.Manager.APIKey == "" {
		return fmt.Errorf("manager.api_key is required")
	}
	if c.TestServer.URL == "" {
		return fmt.Errorf("testServer.url is required")
	}

	// At least one test type must be enabled
	if !c.Tests.HTTP.Enabled && !c.Tests.TCP.Enabled && !c.Tests.UDP.Enabled && !c.Tests.ICMP.Enabled {
		return fmt.Errorf("at least one test type must be enabled")
	}

	return nil
}

func (c *Config) SetDefaults() {
	// Manager defaults
	if c.Manager.URL == "" {
		c.Manager.URL = "https://waddleperf.penguintech.io"
	}
	if c.Manager.AccessTokenPath == "" {
		home, err := os.UserHomeDir()
		if err == nil {
			c.Manager.AccessTokenPath = filepath.Join(home, ".waddleperf", "access_token")
		}
	}
	if c.Manager.RefreshTokenPath == "" {
		home, err := os.UserHomeDir()
		if err == nil {
			c.Manager.RefreshTokenPath = filepath.Join(home, ".waddleperf", "refresh_token")
		}
	}

	// HTTP defaults
	if c.Tests.HTTP.Enabled {
		if c.Tests.HTTP.Protocol == "" {
			c.Tests.HTTP.Protocol = "auto"
		}
		if c.Tests.HTTP.Timeout == 0 {
			c.Tests.HTTP.Timeout = 30
		}
		if c.Tests.HTTP.Advanced.Method == "" {
			c.Tests.HTTP.Advanced.Method = "GET"
		}
		if c.Tests.HTTP.Advanced.UserAgent == "" {
			c.Tests.HTTP.Advanced.UserAgent = "WaddlePerf-GoClient/1.0"
		}
		if c.Tests.HTTP.Advanced.MaxRedirects == 0 {
			c.Tests.HTTP.Advanced.MaxRedirects = 10
		}
	}

	// TCP defaults
	if c.Tests.TCP.Enabled {
		if c.Tests.TCP.Timeout == 0 {
			c.Tests.TCP.Timeout = 10
		}
		if c.Tests.TCP.Advanced.RetryAttempts == 0 {
			c.Tests.TCP.Advanced.RetryAttempts = 3
		}
	}

	// UDP defaults
	if c.Tests.UDP.Enabled {
		if c.Tests.UDP.Timeout == 0 {
			c.Tests.UDP.Timeout = 5
		}
		if c.Tests.UDP.Advanced.RetryAttempts == 0 {
			c.Tests.UDP.Advanced.RetryAttempts = 3
		}
	}

	// ICMP defaults
	if c.Tests.ICMP.Enabled {
		if c.Tests.ICMP.Protocol == "" {
			c.Tests.ICMP.Protocol = "ping"
		}
		if c.Tests.ICMP.Count == 0 {
			c.Tests.ICMP.Count = 4
		}
		if c.Tests.ICMP.Timeout == 0 {
			c.Tests.ICMP.Timeout = 10
		}
		if c.Tests.ICMP.Advanced.TracerouteMaxHops == 0 {
			c.Tests.ICMP.Advanced.TracerouteMaxHops = 30
		}
	}

	// Schedule defaults
	if c.Schedule.IntervalSeconds == 0 {
		c.Schedule.IntervalSeconds = 300 // 5 minutes
	}

	// Logging defaults
	if c.Logging.Level == "" {
		c.Logging.Level = "info"
	}
	if c.Logging.Console {
		// Console logging is enabled by default if not specified
	}
}

func (c *Config) Save(path string) error {
	data, err := yaml.Marshal(c)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	if err := os.WriteFile(path, data, 0600); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

func DefaultConfigPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return "waddleperf-config.yaml"
	}
	return filepath.Join(home, ".waddleperf", "config.yaml")
}

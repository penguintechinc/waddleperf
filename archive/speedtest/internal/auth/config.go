package auth

import "os"

type Config struct {
	JWTSecret       string
	BasicAuthUser   string
	BasicAuthPass   string
	EnableBasicAuth bool
	EnableJWT       bool
}

func LoadConfig() *Config {
	jwtSecret := os.Getenv("JWT_SECRET")
	basicUser := os.Getenv("SPEEDTEST_USER")
	basicPass := os.Getenv("SPEEDTEST_PASS")

	return &Config{
		JWTSecret:       jwtSecret,
		BasicAuthUser:   basicUser,
		BasicAuthPass:   basicPass,
		EnableBasicAuth: basicUser != "" && basicPass != "",
		EnableJWT:       jwtSecret != "",
	}
}

package middleware

import (
	"crypto/subtle"
	"net/http"

	"github.com/penguincloud/waddleperf/speedtest/internal/auth"
)

type AuthMiddleware struct {
	config *auth.Config
}

func NewAuthMiddleware(config *auth.Config) *AuthMiddleware {
	return &AuthMiddleware{config: config}
}

func (m *AuthMiddleware) Authenticate(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !m.config.EnableBasicAuth && !m.config.EnableJWT {
			next.ServeHTTP(w, r)
			return
		}

		if m.config.EnableJWT {
			authHeader := r.Header.Get("Authorization")
			if authHeader != "" {
				if err := auth.ValidateJWT(authHeader, m.config.JWTSecret); err == nil {
					next.ServeHTTP(w, r)
					return
				}
			}
		}

		if m.config.EnableBasicAuth {
			username, password, ok := r.BasicAuth()
			if ok {
				usernameMatch := subtle.ConstantTimeCompare([]byte(username), []byte(m.config.BasicAuthUser)) == 1
				passwordMatch := subtle.ConstantTimeCompare([]byte(password), []byte(m.config.BasicAuthPass)) == 1

				if usernameMatch && passwordMatch {
					next.ServeHTTP(w, r)
					return
				}
			}

			w.Header().Set("WWW-Authenticate", `Basic realm="WaddlePerf Speed Test"`)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		http.Error(w, "Unauthorized", http.StatusUnauthorized)
	})
}

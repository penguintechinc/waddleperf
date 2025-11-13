package auth

import (
	"errors"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

var (
	ErrInvalidToken = errors.New("invalid token")
	ErrExpiredToken = errors.New("token expired")
)

func ValidateJWT(tokenString, secret string) error {
	if secret == "" {
		return errors.New("JWT secret not configured")
	}

	tokenString = strings.TrimPrefix(tokenString, "Bearer ")

	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, ErrInvalidToken
		}
		return []byte(secret), nil
	})

	if err != nil {
		if errors.Is(err, jwt.ErrTokenExpired) {
			return ErrExpiredToken
		}
		return ErrInvalidToken
	}

	if !token.Valid {
		return ErrInvalidToken
	}

	return nil
}

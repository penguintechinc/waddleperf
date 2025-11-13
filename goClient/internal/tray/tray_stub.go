// +build !cgo

package tray

import (
	"fmt"

	"github.com/penguintechinc/WaddlePerf/goClient/internal/config"
)

type TrayApp struct{}

func NewTrayApp(cfg *config.Config) (*TrayApp, error) {
	return nil, fmt.Errorf("system tray support requires CGO and is not available in this build. Use 'daemon' mode instead")
}

func (t *TrayApp) Run() {
	// No-op
}

func (t *TrayApp) onReady() {
	// No-op
}

func (t *TrayApp) onExit() {
	// No-op
}

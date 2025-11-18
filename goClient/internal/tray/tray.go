// +build cgo

package tray

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/getlantern/systray"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/config"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/device"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/scheduler"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/uploader"
)

type TrayApp struct {
	config     *config.Config
	scheduler  *scheduler.Scheduler
	ctx        context.Context
	cancelFunc context.CancelFunc
}

func NewTrayApp(cfg *config.Config) (*TrayApp, error) {
	// Get device info
	deviceInfo, err := device.GetDeviceInfo(cfg.Device.Serial, cfg.Device.Hostname)
	if err != nil {
		return nil, fmt.Errorf("failed to get device info: %w", err)
	}

	// Create uploader
	upl := uploader.NewUploader(cfg.Manager.URL, cfg.Manager.APIKey)

	// Test connection
	if err := upl.TestConnection(); err != nil {
		log.Printf("Warning: Failed to connect to manager: %v", err)
	}

	// Create scheduler
	sched := scheduler.NewScheduler(cfg, upl, deviceInfo)

	ctx, cancel := context.WithCancel(context.Background())

	return &TrayApp{
		config:     cfg,
		scheduler:  sched,
		ctx:        ctx,
		cancelFunc: cancel,
	}, nil
}

func (t *TrayApp) Run() {
	systray.Run(t.onReady, t.onExit)
}

func (t *TrayApp) onReady() {
	systray.SetTitle("WaddlePerf")
	systray.SetTooltip("WaddlePerf Network Monitoring")

	// Menu items
	mStatus := systray.AddMenuItem("Status: Initializing", "Current status")
	mStatus.Disable()

	systray.AddSeparator()

	mRunNow := systray.AddMenuItem("Run Tests Now", "Execute tests immediately")
	mToggle := systray.AddMenuItem("Pause Monitoring", "Pause/Resume scheduled tests")

	systray.AddSeparator()

	mStats := systray.AddMenuItem("View Statistics", "Show test statistics")
	mConfig := systray.AddMenuItem("Configuration", "Show current configuration")

	systray.AddSeparator()

	mQuit := systray.AddMenuItem("Quit", "Exit WaddlePerf")

	// Start scheduler if enabled
	isSchedulerRunning := false
	if t.config.Schedule.Enabled {
		if err := t.scheduler.Start(t.ctx); err != nil {
			log.Printf("Failed to start scheduler: %v", err)
			mStatus.SetTitle("Status: Error")
		} else {
			mStatus.SetTitle("Status: Monitoring")
			isSchedulerRunning = true
		}
	} else {
		mStatus.SetTitle("Status: Manual Mode")
	}

	// Handle menu events
	go func() {
		for {
			select {
			case <-mRunNow.ClickedCh:
				log.Println("Running tests manually...")
				mStatus.SetTitle("Status: Running Tests")
				go func() {
					if err := t.scheduler.RunTests(); err != nil {
						log.Printf("Test execution failed: %v", err)
						mStatus.SetTitle("Status: Test Failed")
					} else {
						if isSchedulerRunning {
							mStatus.SetTitle("Status: Monitoring")
						} else {
							mStatus.SetTitle("Status: Manual Mode")
						}
					}
				}()

			case <-mToggle.ClickedCh:
				if isSchedulerRunning {
					t.scheduler.Stop()
					isSchedulerRunning = false
					mToggle.SetTitle("Resume Monitoring")
					mStatus.SetTitle("Status: Paused")
					log.Println("Scheduler paused")
				} else {
					if err := t.scheduler.Start(t.ctx); err != nil {
						log.Printf("Failed to start scheduler: %v", err)
						mStatus.SetTitle("Status: Error")
					} else {
						isSchedulerRunning = true
						mToggle.SetTitle("Pause Monitoring")
						mStatus.SetTitle("Status: Monitoring")
						log.Println("Scheduler resumed")
					}
				}

			case <-mStats.ClickedCh:
				stats := t.scheduler.GetStats()
				log.Printf("Statistics: %+v", stats)

			case <-mConfig.ClickedCh:
				log.Printf("Configuration:")
				log.Printf("  Manager URL: %s", t.config.Manager.URL)
				log.Printf("  TestServer URL: %s", t.config.TestServer.URL)
				log.Printf("  Schedule Interval: %d seconds", t.config.Schedule.IntervalSeconds)
				log.Printf("  HTTP Tests: %v", t.config.Tests.HTTP.Enabled)
				log.Printf("  TCP Tests: %v", t.config.Tests.TCP.Enabled)
				log.Printf("  UDP Tests: %v", t.config.Tests.UDP.Enabled)
				log.Printf("  ICMP Tests: %v", t.config.Tests.ICMP.Enabled)

			case <-mQuit.ClickedCh:
				log.Println("Quitting WaddlePerf...")
				systray.Quit()
				return

			case <-t.ctx.Done():
				return
			}
		}
	}()
}

func (t *TrayApp) onExit() {
	log.Println("Exiting system tray")
	t.scheduler.Stop()
	t.cancelFunc()
	os.Exit(0)
}

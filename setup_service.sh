#!/bin/bash
# Setup ASL Scraper as a systemd service on EC2

echo "Setting up ASL Scraper as a system service..."

# Copy service file to systemd
sudo cp asl-scraper.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable asl-scraper.service

echo "✅ Service installed!"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start asl-scraper"
echo "  Stop:    sudo systemctl stop asl-scraper"
echo "  Status:  sudo systemctl status asl-scraper"
echo "  Logs:    sudo journalctl -u asl-scraper -f"
echo "  Restart: sudo systemctl restart asl-scraper"
echo ""
echo "Your scraper will now run independently and restart on failure!"


#!/bin/bash
# Alternative: Run scraper in background using screen

echo "Starting ASL Scraper in screen session..."

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    echo "Installing screen..."
    sudo apt install -y screen
fi

# Kill existing session if exists
screen -S asl-scraper -X quit 2>/dev/null || true

# Start new screen session
screen -dmS asl-scraper bash -c 'cd /home/ubuntu/cyfer-signs && python3 scraper.py 2>&1 | tee logs/screen.log'

echo "✅ Scraper started in background!"
echo ""
echo "Commands:"
echo "  Attach:  screen -r asl-scraper"
echo "  Detach:  Press Ctrl+A then D"
echo "  Kill:    screen -X -S asl-scraper quit"
echo "  View log: tail -f logs/screen.log"


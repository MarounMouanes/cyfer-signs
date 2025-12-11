# Running ASL Scraper in Background

Your scraper needs to run for hours/days without keeping your terminal open. Here are the options:

---

## ⭐ Option 1: Systemd Service (Recommended)

**Best for:** Production use, auto-restart on failure, survives reboots

### Setup:
```bash
# On EC2 instance
cd cyfer-signs
./setup_service.sh
```

### Control:
```bash
# Start scraper
sudo systemctl start asl-scraper

# Check status
sudo systemctl status asl-scraper

# View live logs
sudo journalctl -u asl-scraper -f

# Stop scraper
sudo systemctl stop asl-scraper

# Restart scraper
sudo systemctl restart asl-scraper

# Disable auto-start on boot
sudo systemctl disable asl-scraper
```

### Features:
✅ Runs independently of SSH connection  
✅ Auto-restarts on crash  
✅ Starts automatically on server reboot  
✅ Managed logs with journalctl  
✅ Standard Linux service management  

---

## 🖥️ Option 2: Screen Session

**Best for:** Quick testing, easy to attach/detach

### Setup:
```bash
# On EC2 instance
cd cyfer-signs
./run_background.sh
```

### Control:
```bash
# View running sessions
screen -ls

# Attach to session
screen -r asl-scraper

# Detach (while attached)
Ctrl+A, then D

# Kill session
screen -X -S asl-scraper quit

# View logs
tail -f logs/screen.log
```

### Features:
✅ Easy to attach and see live output  
✅ Survives SSH disconnection  
⚠️ Dies if server reboots  
⚠️ No auto-restart on crash  

---

## 🔄 Option 3: Nohup (Simple)

**Best for:** One-off runs, simplest method

### Usage:
```bash
cd cyfer-signs
nohup python3 scraper.py > logs/nohup.log 2>&1 &

# Get process ID
ps aux | grep scraper.py

# View logs
tail -f logs/nohup.log

# Kill process
kill <PID>
```

### Features:
✅ Simplest to use  
✅ Survives SSH disconnection  
⚠️ Dies if server reboots  
⚠️ No auto-restart on crash  
⚠️ Harder to manage  

---

## 📊 Option 4: AWS Lambda + Step Functions (Advanced)

**Best for:** Scheduled runs, serverless, cost optimization

Would require refactoring the scraper to:
- Break into smaller chunks (Lambda 15-min timeout)
- Use Step Functions for orchestration
- Store state in DynamoDB

**Not needed for this use case** - EC2 with systemd is better.

---

## 🔥 Option 5: Docker + Docker Compose (Containerized)

**Best for:** Portability, multiple environments

### Setup:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "scraper.py"]
```

**Not needed for this use case** - adds unnecessary complexity.

---

## 📈 Monitoring & Management

### Check Scraper Progress:
```bash
# View progress file
cat progress.json | python3 -m json.tool

# Count completed videos
grep -c "completed" progress.json

# View recent logs
tail -100 logs/scraper_*.log

# Check S3 uploads
aws s3 ls s3://asl-signs-videos/ --recursive | wc -l
```

### System Resources:
```bash
# Check CPU/Memory usage
top
htop

# Check disk space
df -h

# Check network usage
sudo iftop
```

### If Something Goes Wrong:
```bash
# Systemd service
sudo systemctl status asl-scraper
sudo journalctl -u asl-scraper --no-pager | tail -100

# Screen
screen -r asl-scraper

# Check for crashed Python processes
ps aux | grep python3

# Kill stuck processes
sudo pkill -f scraper.py
```

---

## 🎯 Recommended Setup

For your use case (scraping 39,000 videos over several hours):

**Use Systemd Service:**

1. **Initial setup:**
```bash
cd cyfer-signs
./setup_service.sh
```

2. **Start scraping:**
```bash
sudo systemctl start asl-scraper
```

3. **Monitor (open multiple SSH sessions if you want):**
```bash
# Terminal 1: Live logs
sudo journalctl -u asl-scraper -f

# Terminal 2: Watch progress
watch -n 10 'cat progress.json | python3 -m json.tool'

# Terminal 3: S3 count
watch -n 60 'aws s3 ls s3://asl-signs-videos/ --recursive | wc -l'
```

4. **Disconnect:** Close terminal, go to sleep, come back later!

5. **Check when done:**
```bash
sudo systemctl status asl-scraper
cat progress.json | python3 -m json.tool
```

---

## ⚠️ Important Notes

### Git Push Issues:
The service can't push to GitHub automatically (no credentials in background).

**Options:**
1. **Disable git push** (metadata stays on EC2, upload later)
2. **Use SSH keys** for GitHub authentication
3. **Pull metadata from EC2** when done:
   ```bash
   scp -i asl-scraper-key.pem -r ubuntu@3.236.22.95:/home/ubuntu/cyfer-signs/metadata .
   ```

### Cost Management:
- EC2 charges by the hour (rounded up)
- Stop instance when done: `aws ec2 stop-instances --instance-ids i-xxx`
- Restart when needed: `aws ec2 start-instances --instance-ids i-xxx`

### Free Tier Limits:
- 750 hours/month of t3.micro (31 days × 24 hours = 744 hours)
- You're safe for 24/7 operation in your first year!

---

## 🚀 Quick Start

```bash
# Connect to EC2
ssh -i asl-scraper-key.pem ubuntu@3.236.22.95

# Setup service
cd cyfer-signs
./setup_service.sh

# Start scraping
sudo systemctl start asl-scraper

# Check it's running
sudo systemctl status asl-scraper

# Watch logs
sudo journalctl -u asl-scraper -f

# Disconnect - it keeps running!
exit
```

Done! Come back in 6 hours and check your S3 bucket. 🎉


# Quick Start Guide 🚀

## 30-Second Overview

1. **Create S3 bucket** in AWS console
2. **Launch EC2 instance** with IAM role for S3 access
3. **SSH to EC2** and run setup script
4. **Start scraper** and let it run

---

## Detailed Steps

### 1️⃣ AWS S3 Bucket (2 minutes)

```
1. Go to: https://s3.console.aws.amazon.com/s3/
2. Click "Create bucket"
3. Name: asl-signs-videos (or your choice)
4. Region: us-east-1
5. Keep defaults → Create bucket
```

### 2️⃣ AWS IAM Role (3 minutes)

```
1. Go to: https://console.aws.amazon.com/iam/
2. Roles → Create role
3. Use case: EC2 → Next
4. Permissions: AmazonS3FullAccess → Next
5. Name: ASL-Scraper-EC2-Role → Create
```

### 3️⃣ Launch EC2 (5 minutes)

```
1. Go to: https://console.aws.amazon.com/ec2/
2. Launch Instance
3. Name: ASL-Scraper
4. AMI: Ubuntu 22.04 LTS
5. Type: t2.micro (free) or t2.small
6. Key pair: Create new (download .pem!)
7. Advanced → IAM profile: ASL-Scraper-EC2-Role
8. Launch!
```

### 4️⃣ Connect to EC2

```bash
# Windows (Git Bash) or Mac/Linux
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### 5️⃣ Setup on EC2

```bash
# Run automated setup
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/ec2_setup.sh | bash

# OR manual setup:
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git
git clone YOUR_REPO_URL
cd YOUR_REPO
pip3 install -r requirements.txt
```

### 6️⃣ Configure

```bash
nano config.json
# Update s3_bucket_name if you used a different name
```

### 7️⃣ Run!

```bash
# Test with one letter
python3 scraper.py --letters a

# Run all letters in background
nohup python3 scraper.py > output.log 2>&1 &

# Monitor
tail -f logs/scraper_*.log
```

---

## Even Faster: Screen Method

```bash
# Install screen
sudo apt install -y screen

# Start session
screen -S scraper

# Run scraper
python3 scraper.py

# Detach: Ctrl+A then D
# Reattach later: screen -r scraper
```

---

## Multiple Instances for Speed

### EC2 Instance #1:
```bash
python3 scraper.py --letters a b c d e f g h i j k l m
```

### EC2 Instance #2:
```bash
python3 scraper.py --letters n o p q r s t u v w x y z
```

Both push to same GitHub repo - doubles speed!

---

## Monitoring

```bash
# Live logs
tail -f logs/scraper_*.log

# Progress
cat progress.json | python3 -m json.tool

# S3 contents
aws s3 ls s3://asl-signs-videos/ --recursive | wc -l
```

---

## Troubleshooting

### "S3 access denied"
→ Check IAM role is attached to EC2 instance

### "Git push failed"
→ Use personal access token: `git remote set-url origin https://TOKEN@github.com/USER/REPO.git`

### Out of memory
→ Reduce `num_workers` in config.json

---

## When Complete

Your S3 bucket will have:
- ~39,000 videos (~4.5 GB)
- Organized by letter: `a/abandon.mp4`, `b/baby.mp4`, etc.

Your GitHub will have:
- ~39,000 metadata JSON files
- Complete progress tracking
- Full scraping history

**Estimated Time:** 3-6 hours depending on workers and instance type

---

That's it! 🎉


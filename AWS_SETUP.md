# AWS Setup Guide for ASL Video Scraper

## Overview
This guide will help you set up:
1. **S3 Bucket** - To store the scraped videos
2. **EC2 Instance** - To run the scraper
3. **IAM Permissions** - For EC2 to access S3

---

## Step 1: Create S3 Bucket

### Via AWS Console:
1. Go to https://console.aws.amazon.com/s3/
2. Click **"Create bucket"**
3. **Bucket name**: `asl-signs-videos` (must be globally unique, change if needed)
4. **Region**: Choose `us-east-1` or your preferred region
5. **Block Public Access**: Keep all blocks enabled (videos will be private)
6. Click **"Create bucket"**

### Via AWS CLI (alternative):
```bash
aws s3 mb s3://asl-signs-videos --region us-east-1
```

**Note**: If the bucket name is taken, choose a different name and update `config.json`

---

## Step 2: Create IAM Role for EC2

This allows your EC2 instance to upload to S3 without storing credentials.

### Via AWS Console:
1. Go to https://console.aws.amazon.com/iam/
2. Click **"Roles"** → **"Create role"**
3. **Trusted entity type**: AWS service
4. **Use case**: EC2
5. Click **"Next"**
6. **Attach permissions**: Search and select `AmazonS3FullAccess` (or create custom policy)
7. Click **"Next"**
8. **Role name**: `ASL-Scraper-EC2-Role`
9. Click **"Create role"**

### Custom Policy (More Secure):
Instead of `AmazonS3FullAccess`, create a custom policy with minimal permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::asl-signs-videos",
        "arn:aws:s3:::asl-signs-videos/*"
      ]
    }
  ]
}
```

---

## Step 3: Launch EC2 Instance

### Via AWS Console:
1. Go to https://console.aws.amazon.com/ec2/
2. Click **"Launch Instance"**

#### Configure Instance:
- **Name**: `ASL-Scraper`
- **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
- **Instance type**: `t2.micro` (free tier) or `t2.small` (recommended)
- **Key pair**: Create new or select existing (download .pem file!)
- **Network settings**: Allow SSH (port 22) from your IP
- **Storage**: 8 GB (free tier) or 20 GB recommended
- **Advanced details**:
  - **IAM instance profile**: Select `ASL-Scraper-EC2-Role`

3. Click **"Launch instance"**
4. Wait for instance state to be "running"

### Note the Instance Details:
- **Instance ID**: (e.g., i-1234567890abcdef0)
- **Public IPv4 address**: (e.g., 3.145.123.45)

---

## Step 4: Connect to EC2 Instance

### On Windows (using Git Bash):
```bash
# Change permissions on your key file
chmod 400 /path/to/your-key.pem

# Connect via SSH
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### On Mac/Linux:
```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## Step 5: Setup EC2 Instance

Once connected to your EC2 instance, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install -y python3 python3-pip git

# Install AWS CLI (if needed)
sudo apt install -y awscli

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Install Python dependencies
pip3 install -r requirements.txt

# Test S3 access
aws s3 ls s3://asl-signs-videos/
```

---

## Step 6: Configure Scraper

Edit `config.json` if needed:

```bash
nano config.json
```

Update these fields:
- `s3_bucket_name`: Your bucket name (if different)
- `aws_region`: Your bucket's region
- `num_workers`: 4-8 (depending on instance size)

---

## Step 7: Run the Scraper

### Option A: Run in foreground (for testing)
```bash
python3 scraper.py
```

### Option B: Run in background (recommended)
```bash
nohup python3 scraper.py > scraper_output.log 2>&1 &
```

### Option C: Use screen (can detach/reattach)
```bash
# Install screen
sudo apt install -y screen

# Start screen session
screen -S asl-scraper

# Run scraper
python3 scraper.py

# Detach: Press Ctrl+A, then D
# Reattach: screen -r asl-scraper
```

### Monitor Progress:
```bash
# Watch log file
tail -f logs/scraper_*.log

# Check progress file
cat progress.json | python3 -m json.tool
```

---

## Step 8: Run Multiple Instances (Optional)

To speed up scraping, run multiple EC2 instances with different letter ranges:

### Instance 1:
```bash
python3 scraper.py --letters a b c d e f g h i j k l m
```

### Instance 2:
```bash
python3 scraper.py --letters n o p q r s t u v w x y z
```

Each instance will push to the same GitHub repo but process different letters.

---

## Cost Estimates

### Free Tier (First 12 months):
- **EC2**: 750 hours/month of t2.micro (one instance running 24/7)
- **S3**: 5 GB storage, 20,000 GET requests, 2,000 PUT requests
- **Data Transfer**: 15 GB out

### Expected Costs:
- **S3 Storage**: ~$0.12/month for 5 GB
- **Data Transfer**: ~$0 (within free tier)
- **EC2 (t2.small if needed)**: ~$16/month

### For 4.5 GB of videos:
- **Storage**: ~$0.10/month
- **Upload**: Free (PUT requests in free tier)
- **Total**: Nearly free if using t2.micro!

---

## Troubleshooting

### S3 Upload Fails:
```bash
# Check IAM role is attached
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://asl-signs-videos/
```

### Out of Memory:
- Reduce `num_workers` in config.json
- Use larger instance type (t2.small or t2.medium)

### Git Push Fails:
```bash
# Setup SSH key or use HTTPS with token
git remote set-url origin https://YOUR_TOKEN@github.com/USER/REPO.git
```

### Instance Stops:
- Check AWS billing/limits
- Ensure you're using correct instance type
- Check security group allows SSH

---

## Cleanup (When Done)

### Keep videos, delete EC2:
1. Stop/terminate EC2 instance
2. Keep S3 bucket with videos

### Delete everything:
```bash
# Empty S3 bucket
aws s3 rm s3://asl-signs-videos --recursive

# Delete bucket
aws s3 rb s3://asl-signs-videos

# Terminate EC2 instance via console
```

---

## Security Best Practices

1. ✅ Never commit AWS credentials to Git
2. ✅ Use IAM roles (not access keys) for EC2
3. ✅ Restrict SSH to your IP only
4. ✅ Keep S3 buckets private
5. ✅ Terminate instances when not in use
6. ✅ Enable billing alerts

---

## Support

If you encounter issues:
1. Check logs: `logs/scraper_*.log`
2. Check progress: `progress.json`
3. Check AWS CloudWatch for EC2/S3 metrics
4. Verify IAM permissions


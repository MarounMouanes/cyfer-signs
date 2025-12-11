#!/bin/bash
# Local Setup Script for ASL Video Scraper
# Run this on your local machine before pushing to GitHub

set -e

echo "=================================="
echo "ASL Scraper Local Setup"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n): " create_venv

if [ "$create_venv" = "y" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    # Activate based on OS
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    echo "✅ Virtual environment activated"
fi

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Initialize Git (if not already)
if [ ! -d .git ]; then
    echo "🔧 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: ASL video scraper"
    
    echo ""
    read -p "Enter GitHub repository URL (leave empty to skip): " repo_url
    
    if [ ! -z "$repo_url" ]; then
        git remote add origin "$repo_url"
        git branch -M main
        git push -u origin main
        echo "✅ Pushed to GitHub"
    fi
else
    echo "✅ Git repository already initialized"
fi

# AWS Configuration
echo ""
echo "☁️ AWS Configuration"
read -p "Do you have AWS credentials configured? (y/n): " has_aws

if [ "$has_aws" != "y" ]; then
    echo ""
    echo "You need AWS credentials to upload to S3."
    echo "Options:"
    echo "  1. Run on EC2 with IAM role (recommended)"
    echo "  2. Configure AWS CLI locally: aws configure"
    echo ""
    read -p "Configure AWS CLI now? (y/n): " config_aws
    
    if [ "$config_aws" = "y" ]; then
        aws configure
    fi
fi

# Test S3 access
echo ""
read -p "Test S3 access? (y/n): " test_s3

if [ "$test_s3" = "y" ]; then
    read -p "Enter S3 bucket name: " bucket_name
    
    if aws s3 ls s3://$bucket_name/ 2>/dev/null; then
        echo "✅ S3 access successful!"
    else
        echo "❌ S3 access failed. Check credentials and bucket name."
    fi
fi

# Create sample config (if needed)
if [ ! -f config.json ]; then
    echo "⚠️ config.json not found (should exist from template)"
fi

echo ""
echo "=================================="
echo "✅ Local Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Edit config.json with your settings"
echo "  2. Test locally: python3 scraper.py --letters a"
echo "  3. Or deploy to EC2 (see AWS_SETUP.md)"
echo ""
echo "For AWS/EC2 deployment:"
echo "  1. Follow AWS_SETUP.md to create S3 and EC2"
echo "  2. SSH to EC2 and run: curl -sSL https://raw.githubusercontent.com/YOUR_REPO/main/ec2_setup.sh | bash"
echo ""
echo "=================================="


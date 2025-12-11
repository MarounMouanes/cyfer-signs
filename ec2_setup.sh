#!/bin/bash
# EC2 Instance Setup Script for ASL Video Scraper
# Run this script on your EC2 instance after connecting via SSH

set -e  # Exit on error

echo "=================================="
echo "ASL Scraper EC2 Setup"
echo "=================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and Git..."
sudo apt install -y python3 python3-pip git

# Install AWS CLI
echo "☁️ Installing AWS CLI..."
sudo apt install -y awscli

# Verify installations
echo "✅ Verifying installations..."
python3 --version
pip3 --version
git --version
aws --version

# Configure Git
echo ""
echo "📝 Git Configuration"
read -p "Enter your Git username: " git_username
read -p "Enter your Git email: " git_email

git config --global user.name "$git_username"
git config --global user.email "$git_email"

# Setup SSH key for GitHub (optional)
echo ""
read -p "Do you want to setup SSH key for GitHub? (y/n): " setup_ssh

if [ "$setup_ssh" = "y" ]; then
    echo "🔑 Generating SSH key..."
    ssh-keygen -t ed25519 -C "$git_email" -f ~/.ssh/id_ed25519 -N ""
    
    echo ""
    echo "========================================="
    echo "📋 Your public SSH key (copy this):"
    echo "========================================="
    cat ~/.ssh/id_ed25519.pub
    echo "========================================="
    echo ""
    echo "Add this key to GitHub:"
    echo "1. Go to https://github.com/settings/keys"
    echo "2. Click 'New SSH key'"
    echo "3. Paste the key above"
    echo "4. Click 'Add SSH key'"
    echo ""
    read -p "Press Enter after adding the key to GitHub..."
    
    # Test SSH connection
    ssh -T git@github.com || true
fi

# Clone repository
echo ""
read -p "Enter your GitHub repository URL (HTTPS or SSH): " repo_url

if [ ! -z "$repo_url" ]; then
    echo "📥 Cloning repository..."
    git clone "$repo_url" asl-scraper
    cd asl-scraper
else
    echo "⚠️ No repository URL provided. Please clone manually."
    exit 0
fi

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip3 install -r requirements.txt

# Test S3 access
echo ""
echo "🧪 Testing S3 access..."
read -p "Enter your S3 bucket name (from config.json): " bucket_name

if aws s3 ls s3://$bucket_name/ 2>/dev/null; then
    echo "✅ S3 access successful!"
else
    echo "❌ S3 access failed. Check IAM role is attached to EC2 instance."
    echo "   Go to EC2 console → Actions → Security → Modify IAM role"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p metadata logs

# Display final instructions
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Review config.json: nano config.json"
echo "2. Test the scraper: python3 scraper.py --letters a"
echo "3. Run in background: nohup python3 scraper.py > scraper_output.log 2>&1 &"
echo "4. Or use screen: screen -S asl-scraper && python3 scraper.py"
echo ""
echo "Monitor progress:"
echo "  - tail -f logs/scraper_*.log"
echo "  - cat progress.json | python3 -m json.tool"
echo ""
echo "Happy scraping! 🤟"
echo "=================================="


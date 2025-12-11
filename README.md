# ASL Video Scraper 🤟

A robust, parallel web scraper for collecting American Sign Language (ASL) video demonstrations from [SignASL.org](https://www.signasl.org/). Videos are automatically uploaded to AWS S3 with metadata stored in JSON format.

## Features ✨

- **🚀 Parallel Processing**: Multi-worker architecture for fast scraping
- **☁️ AWS S3 Integration**: Direct upload to S3 bucket
- **📝 Metadata Collection**: Saves sign descriptions, categories, and related signs
- **💾 Progress Tracking**: Resume from where you left off if interrupted
- **🔄 Auto Git Sync**: Commits and pushes progress every N videos
- **🛡️ Robust Error Handling**: Retry logic and comprehensive logging
- **🔧 Configurable**: Easy JSON configuration
- **📊 Real-time Stats**: Track progress with detailed logging

## Quick Start 🏃

### Prerequisites
- Python 3.8+
- AWS Account (free tier works!)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/asl-scraper.git
cd asl-scraper

# Install dependencies
pip install -r requirements.txt

# Configure AWS (if running locally)
aws configure
# OR on EC2, attach IAM role (see AWS_SETUP.md)
```

### Configuration

Edit `config.json`:

```json
{
  "s3_bucket_name": "your-bucket-name",
  "aws_region": "us-east-1",
  "num_workers": 4,
  "letters": ["a", "b", "c", ...],
  "commit_every_n_videos": 10
}
```

### Run

```bash
# Scrape all letters
python3 scraper.py

# Scrape specific letters
python3 scraper.py --letters a b c

# Run in background
nohup python3 scraper.py > output.log 2>&1 &
```

## AWS Setup 🔧

See [AWS_SETUP.md](AWS_SETUP.md) for detailed instructions on:
- Creating S3 bucket
- Setting up EC2 instance
- Configuring IAM roles
- Running the scraper in the cloud

## Project Structure 📁

```
asl-scraper/
├── scraper.py              # Main scraper script
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── progress.json           # Scraping progress (auto-generated)
├── metadata/               # Sign metadata (JSON files)
│   ├── a/
│   │   ├── abandon.json
│   │   └── ...
│   └── b/
│       └── ...
├── logs/                   # Scraping logs
│   └── scraper_YYYYMMDD_HHMMSS.log
├── AWS_SETUP.md           # AWS setup guide
└── README.md              # This file
```

## How It Works 🔍

1. **Task Generation**: Scrapes dictionary pages to build list of all signs
2. **Parallel Processing**: Distributes tasks across multiple worker processes
3. **Video Extraction**: Parses sign pages to extract video URLs and metadata
4. **Download & Upload**: Downloads videos and uploads directly to S3
5. **Metadata Storage**: Saves structured metadata as JSON
6. **Progress Tracking**: Updates progress.json continuously
7. **Git Sync**: Commits metadata and progress every N videos

## Configuration Options ⚙️

| Option | Description | Default |
|--------|-------------|---------|
| `letters` | Letters to scrape | All (a-z) |
| `num_workers` | Parallel workers | 4 |
| `request_delay` | Delay between requests (seconds) | 0.5 |
| `retry_attempts` | Number of retries for failed requests | 3 |
| `retry_delay` | Delay between retries (seconds) | 2 |
| `commit_every_n_videos` | Git commit frequency | 10 |
| `s3_bucket_name` | S3 bucket for videos | `asl-signs-videos` |
| `aws_region` | AWS region | `us-east-1` |
| `save_videos_locally` | Also save videos locally | `false` |
| `upload_to_s3` | Upload to S3 | `true` |

## Metadata Format 📋

Each sign's metadata is saved as JSON:

```json
{
  "sign_name": "abandon",
  "video_url": "https://media.signbsl.com/videos/asl/youtube/mp4/abc123.mp4",
  "s3_key": "a/abandon.mp4",
  "description": "To leave behind; desert; forsake",
  "similar_signs": ["leave", "desert"],
  "categories": ["verbs", "actions"],
  "scraped_at": "2024-12-11T12:34:56.789"
}
```

## Progress Tracking 📊

`progress.json` tracks:
- Completed signs
- Failed signs (with reasons)
- Statistics (success/failure/skip counts)
- Timestamps

Resume scraping anytime - already completed signs are skipped.

## Monitoring 👀

### Watch logs in real-time:
```bash
tail -f logs/scraper_*.log
```

### Check progress:
```bash
cat progress.json | python3 -m json.tool
```

### View S3 contents:
```bash
aws s3 ls s3://your-bucket-name/ --recursive
```

## Performance 🚀

**Estimated Scraping Time:**
- Total signs: ~39,000
- With 4 workers: ~5-6 hours
- With 8 workers: ~3-4 hours

**Storage:**
- Videos: ~4.5 GB total
- Metadata: ~50 MB total

## Multiple Instances 🔄

Speed up scraping by running multiple instances:

```bash
# Machine 1
python3 scraper.py --letters a b c d e f g h i j k l m

# Machine 2
python3 scraper.py --letters n o p q r s t u v w x y z
```

Each pushes to the same GitHub repo - no conflicts!

## Troubleshooting 🔧

### S3 Permission Denied
- Check IAM role/credentials
- Verify bucket name in config.json
- Test: `aws s3 ls s3://your-bucket-name/`

### Git Push Fails
```bash
# Use personal access token
git remote set-url origin https://TOKEN@github.com/USER/REPO.git
```

### Out of Memory
- Reduce `num_workers` in config.json
- Use larger EC2 instance

### Scraper Hangs
- Check internet connection
- Verify website is accessible
- Review logs for errors

## Cost Estimate 💰

**AWS Free Tier (12 months):**
- EC2 t2.micro: 750 hours/month (FREE)
- S3: 5 GB storage (FREE)
- Data transfer: 15 GB/month out (FREE)

**After Free Tier:**
- S3 storage (4.5 GB): ~$0.10/month
- EC2 t2.micro: ~$8.50/month
- **Total: ~$8.60/month**

## Ethical Considerations ⚖️

- Respectful scraping with delays between requests
- Videos are publicly available educational content
- Attribution to SignASL.org maintained in metadata
- For educational/research purposes

## License 📄

MIT License - See LICENSE file

## Contributing 🤝

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Acknowledgments 🙏

- Videos sourced from [SignASL.org](https://www.signasl.org/)
- Community-contributed ASL demonstrations
- Open-source ASL education initiative

## Support 💬

Issues? Questions?
- Open a GitHub issue
- Check AWS_SETUP.md for AWS problems
- Review logs/scraper_*.log for errors

---

**Happy Scraping! 🤟**


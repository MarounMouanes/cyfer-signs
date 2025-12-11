#!/usr/bin/env python3
"""
ASL Signs Video Scraper
Scrapes American Sign Language videos from signasl.org and uploads to S3
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from multiprocessing import Process, Queue, Manager
from queue import Empty
import requests
import cloudscraper
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError
from git import Repo, GitCommandError
from tqdm import tqdm


class ASLScraper:
    """Main scraper class for ASL video collection"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize scraper with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize paths
        self.metadata_dir = Path("metadata")
        self.videos_dir = Path("videos")
        self.progress_file = Path("progress.json")
        
        # Create directories
        self.metadata_dir.mkdir(exist_ok=True)
        if self.config.get("save_videos_locally", False):
            self.videos_dir.mkdir(exist_ok=True)
        
        # Initialize cloudscraper session
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        
        # Initialize S3 client
        if self.config.get("upload_to_s3", True):
            self.s3_client = boto3.client('s3', region_name=self.config['aws_region'])
            self.bucket_name = self.config['s3_bucket_name']
        
        # Initialize Git repo
        try:
            self.repo = Repo('.')
        except Exception as e:
            self.logger.warning(f"Not a git repository: {e}")
            self.repo = None
        
        # Load or initialize progress
        self.progress = self.load_progress()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_progress(self) -> Dict:
        """Load progress from file or create new"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.logger.info("Loading existing progress...")
                return json.load(f)
        return {
            "started_at": datetime.now().isoformat(),
            "completed_signs": [],
            "failed_signs": [],
            "stats": {
                "total_videos": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def save_progress(self):
        """Save progress to file"""
        self.progress["last_updated"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def get_page_content(self, url: str, retries: int = None) -> Optional[str]:
        """Fetch page content with retries"""
        if retries is None:
            retries = self.config['retry_attempts']
        
        for attempt in range(retries):
            try:
                time.sleep(self.config['request_delay'])
                response = self.scraper.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(self.config['retry_delay'] * (attempt + 1))
        return None
    
    def extract_sign_links(self, html: str) -> List[str]:
        """Extract sign links from dictionary page"""
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        # Find all links to sign pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/sign/'):
                sign_name = href.replace('/sign/', '')
                links.append(sign_name)
        
        return list(set(links))  # Remove duplicates
    
    def extract_video_info(self, html: str, sign_name: str) -> Optional[Dict]:
        """Extract video URL and metadata from sign page"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract video URL from meta tags
        video_url = None
        og_video = soup.find('meta', property='og:video')
        if og_video and og_video.get('content'):
            video_url = og_video['content']
        
        if not video_url:
            twitter_video = soup.find('meta', attrs={'name': 'twitter:player:stream'})
            if twitter_video and twitter_video.get('content'):
                video_url = twitter_video['content']
        
        if not video_url:
            return None
        
        # Extract metadata
        metadata = {
            'sign_name': sign_name,
            'video_url': video_url,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract description
        desc = soup.find('div', class_='featurette-heading-sub')
        if desc:
            metadata['description'] = desc.get_text(strip=True)
        
        # Extract similar signs
        similar_section = soup.find('div', string=lambda x: x and 'Similiar / Same:' in x)
        if similar_section:
            similar_links = similar_section.find_all('a')
            metadata['similar_signs'] = [link.get_text(strip=True) for link in similar_links]
        
        # Extract categories
        cat_section = soup.find('div', string=lambda x: x and 'Categories:' in x)
        if cat_section:
            cat_links = cat_section.find_all('a')
            metadata['categories'] = [link.get_text(strip=True) for link in cat_links]
        
        return metadata
    
    def download_video(self, video_url: str) -> Optional[bytes]:
        """Download video content"""
        try:
            response = self.scraper.get(video_url, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.logger.error(f"Failed to download video {video_url}: {e}")
            return None
    
    def upload_to_s3(self, video_content: bytes, s3_key: str) -> bool:
        """Upload video to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=video_content,
                ContentType='video/mp4'
            )
            self.logger.info(f"Uploaded to S3: {s3_key}")
            return True
        except ClientError as e:
            self.logger.error(f"S3 upload failed for {s3_key}: {e}")
            return False
    
    def save_metadata(self, metadata: Dict, letter: str):
        """Save metadata to JSON file"""
        letter_dir = self.metadata_dir / letter
        letter_dir.mkdir(exist_ok=True)
        
        file_path = letter_dir / f"{metadata['sign_name']}.json"
        with open(file_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def git_commit_and_push(self, message: str):
        """Commit and push changes to git"""
        if not self.repo:
            return
        
        try:
            # Add metadata and progress file
            self.repo.index.add(['metadata/*', 'progress.json'])
            
            if self.repo.index.diff("HEAD"):
                self.repo.index.commit(message)
                origin = self.repo.remote('origin')
                origin.push()
                self.logger.info(f"Git: {message}")
        except GitCommandError as e:
            self.logger.error(f"Git operation failed: {e}")
    
    def process_sign(self, sign_name: str, letter: str) -> Tuple[bool, str]:
        """Process a single sign"""
        # Check if already completed
        if sign_name in self.progress['completed_signs']:
            return True, "already_completed"
        
        # Get sign page
        sign_url = f"{self.config['base_url']}/sign/{sign_name}"
        html = self.get_page_content(sign_url)
        
        if not html:
            return False, "failed_to_fetch_page"
        
        # Extract video info
        metadata = self.extract_video_info(html, sign_name)
        
        if not metadata:
            return False, "no_video_found"
        
        # Download video
        video_content = self.download_video(metadata['video_url'])
        
        if not video_content:
            return False, "failed_to_download_video"
        
        # Save/upload video
        video_filename = f"{letter}/{sign_name}.mp4"
        
        if self.config.get("upload_to_s3", True):
            if not self.upload_to_s3(video_content, video_filename):
                return False, "failed_to_upload_s3"
            metadata['s3_key'] = video_filename
        
        if self.config.get("save_videos_locally", False):
            local_dir = self.videos_dir / letter
            local_dir.mkdir(exist_ok=True)
            local_path = local_dir / f"{sign_name}.mp4"
            with open(local_path, 'wb') as f:
                f.write(video_content)
            metadata['local_path'] = str(local_path)
        
        # Save metadata
        self.save_metadata(metadata, letter)
        
        return True, "success"
    
    def worker(self, worker_id: int, task_queue: Queue, stats: Dict):
        """Worker process function"""
        worker_logger = logging.getLogger(f"Worker-{worker_id}")
        local_count = 0
        
        while True:
            try:
                task = task_queue.get(timeout=5)
                if task is None:  # Poison pill
                    break
                
                letter, sign_name = task
                
                success, reason = self.process_sign(sign_name, letter)
                
                if success:
                    if reason != "already_completed":
                        local_count += 1
                        stats['successful'] += 1
                        self.progress['completed_signs'].append(sign_name)
                        worker_logger.info(f"✓ {sign_name} ({reason})")
                    else:
                        stats['skipped'] += 1
                else:
                    stats['failed'] += 1
                    self.progress['failed_signs'].append({
                        'sign_name': sign_name,
                        'reason': reason,
                        'timestamp': datetime.now().isoformat()
                    })
                    worker_logger.error(f"✗ {sign_name} ({reason})")
                
                # Save progress and commit periodically
                if local_count > 0 and local_count % self.config['commit_every_n_videos'] == 0:
                    self.save_progress()
                    self.git_commit_and_push(
                        f"Progress: {letter} - {local_count} videos from worker {worker_id}"
                    )
                
            except Empty:
                continue
            except Exception as e:
                worker_logger.error(f"Worker error: {e}")
                continue
        
        worker_logger.info(f"Worker {worker_id} finished. Processed {local_count} videos.")
    
    def get_all_tasks(self) -> List[Tuple[str, str]]:
        """Generate all scraping tasks"""
        self.logger.info("Building task list...")
        tasks = []
        
        for letter in self.config['letters']:
            self.logger.info(f"Scanning letter: {letter}")
            
            # Get first page to determine total pages
            page_url = f"{self.config['base_url']}/dictionary/{letter}"
            html = self.get_page_content(page_url)
            
            if not html:
                self.logger.error(f"Failed to fetch {letter}")
                continue
            
            # Extract pagination info
            soup = BeautifulSoup(html, 'lxml')
            pagination = soup.find('ul', class_='pagination')
            max_page = 1
            
            if pagination:
                page_links = pagination.find_all('a', href=True)
                for link in page_links:
                    href = link['href']
                    if f'/dictionary/{letter}/' in href:
                        try:
                            page_num = int(href.split('/')[-1])
                            max_page = max(max_page, page_num)
                        except ValueError:
                            continue
            
            self.logger.info(f"Letter {letter}: {max_page} pages")
            
            # Get all sign links from all pages
            for page in range(1, max_page + 1):
                if page == 1:
                    page_url = f"{self.config['base_url']}/dictionary/{letter}"
                else:
                    page_url = f"{self.config['base_url']}/dictionary/{letter}/{page}"
                
                html = self.get_page_content(page_url)
                if html:
                    sign_links = self.extract_sign_links(html)
                    for sign_name in sign_links:
                        tasks.append((letter, sign_name))
        
        self.logger.info(f"Total tasks: {len(tasks)}")
        return tasks
    
    def run(self):
        """Main execution method"""
        self.logger.info("=" * 80)
        self.logger.info("ASL Video Scraper Starting")
        self.logger.info("=" * 80)
        
        # Get all tasks
        all_tasks = self.get_all_tasks()
        
        if not all_tasks:
            self.logger.error("No tasks found!")
            return
        
        # Create task queue
        manager = Manager()
        task_queue = manager.Queue()
        stats = manager.dict()
        stats['successful'] = 0
        stats['failed'] = 0
        stats['skipped'] = 0
        
        # Add tasks to queue
        for task in all_tasks:
            task_queue.put(task)
        
        # Add poison pills for workers
        num_workers = self.config['num_workers']
        for _ in range(num_workers):
            task_queue.put(None)
        
        # Start workers
        self.logger.info(f"Starting {num_workers} workers...")
        workers = []
        for i in range(num_workers):
            p = Process(target=self.worker, args=(i, task_queue, stats))
            p.start()
            workers.append(p)
        
        # Wait for all workers
        for p in workers:
            p.join()
        
        # Final save and commit
        self.save_progress()
        self.git_commit_and_push(
            f"Final: {stats['successful']} videos completed, {stats['failed']} failed"
        )
        
        # Print summary
        self.logger.info("=" * 80)
        self.logger.info("SCRAPING COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total tasks: {len(all_tasks)}")
        self.logger.info(f"Successful: {stats['successful']}")
        self.logger.info(f"Failed: {stats['failed']}")
        self.logger.info(f"Skipped: {stats['skipped']}")
        self.logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='ASL Video Scraper')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--letters', nargs='+', help='Specific letters to scrape (e.g., a b c)')
    args = parser.parse_args()
    
    scraper = ASLScraper(args.config)
    
    # Override letters if specified
    if args.letters:
        scraper.config['letters'] = [l.lower() for l in args.letters]
    
    try:
        scraper.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        scraper.save_progress()
        print("Progress saved. You can resume later.")
    except Exception as e:
        scraper.logger.error(f"Fatal error: {e}", exc_info=True)
        scraper.save_progress()
        sys.exit(1)


if __name__ == "__main__":
    main()


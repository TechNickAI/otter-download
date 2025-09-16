"""
Clean, simple downloader - no defensive programming bullshit
"""

import os
import time
import logging
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

from .auth import OtterAuth
from .utils import slugify

console = Console()
logger = logging.getLogger(__name__)


def generate_frontmatter(speech: Dict[str, Any]) -> str:
    """Generate YAML frontmatter from speech metadata"""
    # Convert timestamps to ISO format
    def timestamp_to_iso(timestamp):
        if timestamp:
            return datetime.fromtimestamp(timestamp).isoformat() + 'Z'
        return None
    
    # Extract speaker information
    speakers = []
    speaker_distribution = {}
    if speech.get('speakers'):
        for speaker in speech['speakers']:
            speaker_name = speaker.get('speaker_name', 'Unknown')
            speakers.append(speaker_name)
            speaker_distribution[speaker_name] = speaker_distribution.get(speaker_name, 0) + 1
    
    # Extract topics from word clouds
    topics = []
    if speech.get('word_clouds'):
        topics = [cloud['word'] for cloud in speech['word_clouds'][:10]]  # Top 10 topics
    
    # Build frontmatter data
    frontmatter_data = {
        'id': speech.get('speech_id', ''),
        'otid': speech.get('otid', ''),
        'date': timestamp_to_iso(speech.get('created_at')),
        'start_time': timestamp_to_iso(speech.get('start_time')),
        'end_time': timestamp_to_iso(speech.get('end_time')),
        'title': speech.get('title', 'Untitled'),
        'speakers': speakers,
        'speaker_analysis': {
            'total_speakers': len(speakers),
            'speaker_distribution': speaker_distribution
        },
        'topics': topics,
        'summary': speech.get('summary', ''),
        'is_meeting_series': speech.get('is_meeting_series', False),
        'has_images': speech.get('hasPhotos', 0) > 0,
        'images_count': speech.get('hasPhotos', 0),
        'source': 'otter',
        'data_source': 'api',
        'transcript_updated_at': timestamp_to_iso(speech.get('transcript_updated_at'))
    }
    
    # Convert to YAML and wrap in frontmatter markers
    yaml_content = yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return f"---\n{yaml_content}---\n\n"


def get_clean_filename(speech: Dict[str, Any], format: str = "txt") -> str:
    """Generate clean filename: Title_{speech_id}.format"""
    title = speech['title'] or 'Untitled'
    speech_id = speech['speech_id']  # Clean ID without underscores
    slug = slugify(title, max_length=80)
    return f"{slug}_{speech_id}.{format}"


def speech_already_downloaded(speech_id: str, download_folder: Path, format: str = "txt") -> bool:
    """Check if speech already downloaded by looking for speech_id in filename"""
    pattern = f"*_{speech_id}.{format}"
    matches = list(download_folder.glob(pattern))
    return len(matches) > 0


def set_file_timestamp(filepath: Path, speech: Dict[str, Any]):
    """Set file modification time to speech creation time"""
    created_at = speech.get('created_at') or speech.get('start_time') or speech.get('displayed_start_time')
    if created_at and isinstance(created_at, (int, float)):
        timestamp = float(created_at)
        os.utime(filepath, (timestamp, timestamp))


def download_speech(auth: OtterAuth, speech: Dict[str, Any], download_folder: Path, format: str = "txt") -> bool:
    """Download a single speech with optimal LLM-friendly formatting"""
    otid = speech['otid']  # API needs otid for download
    speech_id = speech['speech_id']  # We use speech_id for filename
    filename = get_clean_filename(speech, format)
    filepath = download_folder / filename
    
    # Make direct API call with optimal parameters for LLM processing
    download_url = auth.otter.API_BASE_URL + 'bulk_export'
    payload = {
        'userid': auth.otter._userid,
        'speaker_names': 1,  # Include speaker names
        'speaker_timestamps': 0,  # NO timestamps (better for LLM)
        'merge_same_speaker_segments': 1,  # Combine same speaker paragraphs
        'show_highlights': 0,  # No highlights
        'inline_pictures': 0,
        'monologue': 0,
        'highlight_only': 0,
        'branding': 'false',
        'annotations': 0
    }
    
    data = {
        'formats': format,
        'speech_otid_list': [otid]
    }
    
    headers = {
        'x-csrftoken': auth.otter._cookies['csrftoken'], 
        'referer': 'https://otter.ai/'
    }
    
    response = auth.otter._session.post(download_url, params=payload, headers=headers, data=data)
    
    if response.status_code == 200:
        # Generate frontmatter
        frontmatter = generate_frontmatter(speech)
        
        # Write content with frontmatter
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(response.content.decode('utf-8'))
        
        # Set timestamp
        set_file_timestamp(filepath, speech)
        
        return True
    else:
        console.print(f"❌ Download failed: {speech['title']} (server error {response.status_code})")
        return False


def clean_download_all(
    auth: OtterAuth,
    folder: str = "~/Dropbox/Otter-Export", 
    format: str = "txt",
    overwrite: bool = False,
    sleep_seconds: float = 0.5,
    min_transcript_length: int = 200,
    max_downloads: Optional[int] = None
) -> Dict[str, Any]:
    """
    Simple download: Get speeches, download missing ones
    """
    # Setup
    download_folder = Path(folder).expanduser()
    download_folder.mkdir(parents=True, exist_ok=True)
    
    # Get speeches - use efficient method based on max_downloads
    console.print("📜 Loading your transcript library...")
    
    if max_downloads and max_downloads <= 100:
        # For small counts, use direct API call with page_size to avoid timeouts
        logger.info(f"🔍 Fetching {max_downloads} speeches directly...")
        response = auth.otter.get_speeches(page_size=max_downloads)
        if response and 'data' in response:
            all_speeches = response['data'].get('speeches', [])
        else:
            all_speeches = []
        
        logger.info(f"🎙️ Retrieved {len(all_speeches)} speeches from API")
        
        if all_speeches and len(all_speeches) > 0:
            logger.info(f"📝 First speech title: {all_speeches[0].get('title', 'No title')}")
        
        console.print(f"✅ Found {len(all_speeches)} speeches in your account")
        
        # Stats
        stats = {'total': len(all_speeches), 'downloaded': 0, 'skipped': 0, 'errors': 0, 'filtered': 0}
        
        console.print()
        console.print(Panel.fit(
            f"🚀 Processing {len(all_speeches)} speeches\n"
            f"📁 Format: {format.upper()}\n" 
            f"⏱️  Sleep: {sleep_seconds}s\n"
            f"📏 Min length: {min_transcript_length} chars\n"
            f"📊 Max downloads: {max_downloads or 'All'}",
            border_style="green"
        ))
        
        # Process speeches directly for small counts
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing speeches...", total=len(all_speeches))
            
            for speech in all_speeches:
                if max_downloads and stats['downloaded'] >= max_downloads:
                    console.print(f"🛑 Downloaded maximum limit ({max_downloads} files)")
                    break
                
                title = speech['title'] or 'Untitled'
                speech_id = speech['speech_id']
                
                progress.update(task, description=f"Processing: {title[:40]}...")
                
                # Already downloaded?
                if speech_already_downloaded(speech_id, download_folder, format) and not overwrite:
                    stats['skipped'] += 1
                    progress.advance(task)
                    continue
                
                # Too short?
                transcript = speech.get('transcript', '') or speech.get('summary', '')
                if transcript and len(transcript) < min_transcript_length:
                    stats['filtered'] += 1
                    console.print(f"⏭️ Skipped: {title} (too short - {len(transcript)} chars)")
                    progress.advance(task)
                    continue
                
                # Download it
                if download_speech(auth, speech, download_folder, format):
                    stats['downloaded'] += 1
                    console.print(f"✅ {title}")
                else:
                    stats['errors'] += 1
                
                progress.advance(task)
                
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
    
    else:
        # For large counts or no limit, use batch processing
        logger.info("🔍 Using batch processing for efficient memory usage...")
        
        # Stats
        stats = {'total': 0, 'downloaded': 0, 'skipped': 0, 'errors': 0, 'filtered': 0}
        
        console.print()
        console.print(Panel.fit(
            f"🚀 Processing speeches in batches of 50\n"
            f"📁 Format: {format.upper()}\n" 
            f"⏱️  Sleep: {sleep_seconds}s\n"
            f"📏 Min length: {min_transcript_length} chars\n"
            f"📊 Max downloads: {max_downloads or 'All'}",
            border_style="green"
        ))
        
        # Process speeches in batches
        for batch_num, batch_speeches in enumerate(auth.get_speeches_batch(batch_size=50), 1):
            stats['total'] += len(batch_speeches)
            
            console.print(f"📦 Processing batch {batch_num} ({len(batch_speeches)} speeches)...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task(f"Batch {batch_num}...", total=len(batch_speeches))
                
                for speech in batch_speeches:
                    if max_downloads and stats['downloaded'] >= max_downloads:
                        console.print(f"🛑 Downloaded maximum limit ({max_downloads} files)")
                        return stats
                    
                    title = speech['title'] or 'Untitled'
                    speech_id = speech['speech_id']
                    
                    progress.update(task, description=f"Processing: {title[:40]}...")
                    
                    # Already downloaded?
                    if speech_already_downloaded(speech_id, download_folder, format) and not overwrite:
                        stats['skipped'] += 1
                        progress.advance(task)
                        continue
                    
                    # Too short?
                    transcript = speech.get('transcript', '') or speech.get('summary', '')
                    if transcript and len(transcript) < min_transcript_length:
                        stats['filtered'] += 1
                        console.print(f"⏭️ Skipped: {title} (too short - {len(transcript)} chars)")
                        progress.advance(task)
                        continue
                    
                    # Download it
                    if download_speech(auth, speech, download_folder, format):
                        stats['downloaded'] += 1
                        console.print(f"✅ {title}")
                    else:
                        stats['errors'] += 1
                    
                    progress.advance(task)
                    
                    if sleep_seconds > 0:
                        time.sleep(sleep_seconds)
            
            console.print(f"✅ Completed batch {batch_num}: {stats['downloaded']} total downloads so far")
        
        console.print(f"🎉 All batches completed! Total speeches processed: {stats['total']}")
    
    return stats

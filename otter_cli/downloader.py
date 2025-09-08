"""
Clean, simple downloader - no defensive programming bullshit
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

from .auth import OtterAuth
from .utils import slugify

console = Console()


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
        # Write content directly to target file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
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
    
    # Get speeches - API limit is 530, so use safe default
    fetch_size = max_downloads if max_downloads else 530
    console.print("📜 Loading your transcript library...")
    
    # Use direct API call instead of broken wrapper
    response = auth.otter.get_speeches(page_size=fetch_size)
    data = response.get('data', {})
    all_speeches = data.get('speeches', [])
    
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
    
    # Process speeches
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
            speech_id = speech['speech_id']  # Use clean speech_id for duplicate detection
            
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
    
    return stats

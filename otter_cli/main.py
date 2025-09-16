#!/usr/bin/env python3
"""
Otter AI Transcript Downloader CLI
Beautiful command-line interface for managing Otter.ai transcripts
"""

import getpass
import sys
import logging
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .auth import OtterAuth
from .downloader import clean_download_all

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🦫 Otter AI Transcript Downloader
    
    A beautiful CLI for downloading your Otter.ai transcripts to sync with Dropbox.
    """
    pass


@cli.command()
def login():
    """🔐 Login and list your Otter.ai speeches"""
    
    # Beautiful welcome
    console.print(Panel.fit(
        "[bold blue]🦫 Otter AI Transcript Downloader[/bold blue]\n"
        "[dim]Let's get your transcripts organized, you beautiful human![/dim]",
        border_style="blue"
    ))
    
    console.print()
    
    # Get credentials
    console.print("[bold cyan]Please enter your Otter.ai credentials:[/bold cyan]")
    username = Prompt.ask("📧 [bold]Username/Email[/bold]")
    
    # Secure password input
    console.print("🔒 [bold]Password[/bold] (hidden):")
    password = getpass.getpass("")
    
    console.print()
    
    # Attempt authentication with beautiful spinner
    auth = OtterAuth()
    
    with console.status("[bold green]Connecting to Otter.ai...[/bold green]", spinner="dots"):
        try:
            success = auth.login(username, password)
            
            if success:
                console.print("✅ [bold green]Successfully authenticated![/bold green]")
                console.print()
                
                # Get and display speeches
                console.print("[bold cyan]📜 Loading your transcript library...[/bold cyan]")
                
                with console.status("[bold blue]Getting speech list...[/bold blue]", spinner="dots"):
                    speeches = auth.get_all_speeches()
                
                if speeches:
                    _display_speeches(speeches)
                else:
                    console.print("[yellow]No speeches found in your account.[/yellow]")
                    
            else:
                console.print("❌ [bold red]Authentication failed![/bold red]")
                console.print("[dim]Please check your username and password.[/dim]")
                sys.exit(1)
                
        except Exception as e:
            console.print(f"💥 [bold red]Error:[/bold red] {str(e)}")
            console.print("[dim]Please check your internet connection and try again.[/dim]")
            sys.exit(1)


def _display_speeches(speeches):
    """Display speeches in a beautiful table"""
    
    table = Table(title="🎙️ Your Otter.ai Speeches", show_header=True, header_style="bold cyan")
    table.add_column("Title", style="bold white", width=40)
    table.add_column("Date", style="dim cyan", width=12)
    table.add_column("Duration", style="green", width=10)
    table.add_column("ID", style="dim", width=20)
    
    for speech in speeches[:20]:  # Show first 20 speeches
        # Format the speech data - adjust based on actual API response
        title = str(speech.get('title', 'Untitled'))[:37] + "..." if len(str(speech.get('title', 'Untitled'))) > 40 else str(speech.get('title', 'Untitled'))
        date = str(speech.get('created_at', 'N/A'))[:10]  # Just the date part
        duration = str(speech.get('duration', 'N/A'))
        speech_id = str(speech.get('id', 'N/A'))
        
        table.add_row(title, date, duration, speech_id)
    
    console.print()
    console.print(table)
    
    if len(speeches) > 20:
        console.print(f"[dim]... and {len(speeches) - 20} more speeches[/dim]")
    
    console.print()
    console.print(f"[bold green]Found {len(speeches)} total speeches in your account![/bold green]")


@cli.command()
@click.option('--folder', '-f', default='~/Dropbox/Otter-Export', help='Download folder (default: ~/Dropbox/Otter-Export)')
@click.option('--format', '-fmt', default='txt', type=click.Choice(['txt', 'pdf', 'srt', 'docx']), help='File format to download')
@click.option('--overwrite', '-o', is_flag=True, help='Overwrite existing files')
@click.option('--sleep', '-s', default=0.5, type=float, help='Seconds to sleep between downloads (default: 0.5)')
@click.option('--min-length', '-l', default=200, type=int, help='Minimum transcript length to download (default: 200 chars)')
@click.option('--max-count', '-m', type=int, help='Maximum number of files to download (for testing)')
@click.option('--force', is_flag=True, help='Force full re-download, ignore existing files')
@click.option('--username', '-u', help='Otter.ai username/email')
@click.option('--password', '-p', help='Otter.ai password')
@click.option('--verbosity', '-v', is_flag=True, help='Enable verbose debugging output')
def download(folder, format, overwrite, sleep, min_length, max_count, force, username, password, verbosity):
    """📥 Download all your Otter.ai transcripts"""
    
    # Set up logging level based on verbosity flag
    if verbosity:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console.print("🔍 [bold yellow]Verbose debugging enabled[/bold yellow]")
    else:
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    console.print(Panel.fit(
        "[bold blue]📥 Otter AI Transcript Downloader[/bold blue]\n"
        "[dim]Let's get ALL your transcripts organized, beautiful![/dim]",
        border_style="blue"
    ))
    
    console.print()
    
    # Get credentials if not provided
    if not username or not password:
        console.print("[bold cyan]Please enter your Otter.ai credentials:[/bold cyan]")
        
        if not username:
            username = Prompt.ask("📧 [bold]Username/Email[/bold]")
        
        if not password:
            console.print("🔒 [bold]Password[/bold] (hidden):")
            password = getpass.getpass("")
    
    console.print()
    
    # Authenticate
    auth = OtterAuth()
    
    with console.status("[bold green]Connecting to Otter.ai...[/bold green]", spinner="dots"):
        try:
            success = auth.login(username, password)
            
            if not success:
                console.print("❌ [bold red]Authentication failed![/bold red]")
                console.print("[dim]Please check your username and password.[/dim]")
                sys.exit(1)
                
            console.print("✅ [bold green]Successfully authenticated![/bold green]")
            
        except Exception as e:
            console.print(f"💥 [bold red]Authentication error:[/bold red] {str(e)}")
            sys.exit(1)
    
    # Show download plan
    console.print()
    console.print("[bold cyan]📋 Download Plan:[/bold cyan]")
    console.print(f"   • Format: {format.upper()}")
    console.print(f"   • Folder: {folder}")
    console.print(f"   • Overwrite existing: {'Yes' if overwrite else 'No'}")
    console.print(f"   • Min transcript length: {min_length} chars")
    console.print(f"   • Sleep between downloads: {sleep}s")
    console.print(f"   • Max downloads: {'All speeches' if not max_count else f'{max_count} (testing)'}")
    if force:
        console.print(f"   • Force mode: Download all speeches")
    
    console.print()
    
    # Start download - let it fail properly
    stats = clean_download_all(
        auth=auth,
        folder=folder,
        format=format,
        overwrite=overwrite,
        sleep_seconds=sleep,
        min_transcript_length=min_length,
        max_downloads=max_count
    )
    
    # Show summary
    console.print()
    console.print(Panel.fit(
        f"🎉 [bold green]Download Complete![/bold green]\n\n"
        f"📊 [bold]Summary:[/bold]\n"
        f"   • Total speeches: {stats['total']}\n"
        f"   • Downloaded: [green]{stats['downloaded']}[/green]\n"
        f"   • Skipped: [yellow]{stats['skipped']}[/yellow]\n"
        f"   • Skipped (too short): [blue]{stats['filtered']}[/blue]\n"
        f"   • Errors: [red]{stats['errors']}[/red]\n\n"
        f"📁 Files saved to: [cyan]{folder}[/cyan]",
        border_style="green",
        title="Download Summary"
    ))


if __name__ == "__main__":
    cli()

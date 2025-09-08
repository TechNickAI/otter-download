# 🦫 Otter AI Transcript Downloader

A beautiful command-line tool for downloading and organizing your Otter.ai transcripts. Perfect for syncing with Dropbox, feeding into LLMs, or creating local transcript archives.

## ✨ Features

- 🔐 **Secure Authentication**: Safe login with Otter.ai credentials
- 🎨 **Beautiful CLI**: Rich terminal interface with progress bars and status updates  
- 📁 **Smart Organization**: Downloads to `~/Dropbox/Otter-Export` by default
- 🧠 **LLM-Optimized Format**: Clean transcripts without timestamps, merged speaker segments
- 🏷️ **Clean Filenames**: Human-readable titles with unique IDs: `Meeting-Name_2CAQZKX4X5V5YILZ.txt`
- ⏰ **File Timestamps**: Set to actual speech creation time for chronological sorting
- 🔄 **Smart Resume**: Skip already downloaded transcripts automatically
- 📏 **Content Filtering**: Skip transcripts shorter than 200 characters  
- ⚡ **Rate Limited**: Configurable delays to be respectful to Otter.ai servers

## 🚀 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd otter-download

# Create virtual environment
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the CLI tool
pip install -e .
```

## 🎯 Usage

### Basic Download
```bash
# Download all transcripts to default location (~/Dropbox/Otter-Export)
otter-cli download

# Provide credentials inline (optional)
otter-cli download --username your@email.com --password your_password
```

### Advanced Options
```bash
# Custom folder
otter-cli download --folder ~/Documents/Transcripts

# Different format (txt, pdf, srt, docx)  
otter-cli download --format pdf

# Faster downloads (reduce sleep between requests)
otter-cli download --sleep 0.1

# Filter out very short transcripts
otter-cli download --min-length 500

# Testing with limited downloads
otter-cli download --max-count 10
```

### List Available Speeches
```bash
# View your speeches without downloading
otter-cli login
```

## 🔧 Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--folder` | `~/Dropbox/Otter-Export` | Download directory |
| `--format` | `txt` | File format (txt, pdf, srt, docx) |  
| `--sleep` | `0.5` | Seconds between downloads |
| `--min-length` | `200` | Minimum transcript length (chars) |
| `--overwrite` | `false` | Overwrite existing files |
| `--max-count` | `unlimited` | Limit downloads (for testing) |

## 📁 File Organization

**Filename Format**: `{Title}_{SpeechID}.{format}`
- **Example**: `Team-Meeting_2CAQZKX4X5V5YILZ.txt`
- **Benefits**: Human-readable, unique IDs, filesystem-safe

**File Timestamps**: Set to actual speech creation time
- **Benefit**: `ls -t` shows chronological order
- **Benefit**: Finder "Date Modified" sorting works perfectly

**Content Format**: LLM-optimized
```
Speaker Name
Longer paragraphs of merged content from same speaker...

Next Speaker  
More merged content without timestamp clutter...
```

## 🔄 Smart Resume Logic

The tool automatically handles interrupted and incremental downloads:

1. **First Run**: Downloads all available transcripts
2. **Subsequent Runs**: Only downloads new transcripts (by checking existing speech IDs)
3. **Interrupted Downloads**: Resume from where left off automatically

## 🛠 Development

Built with:
- **[Click](https://click.palletsprojects.com/)**: CLI framework
- **[Rich](https://rich.readthedocs.io/)**: Beautiful terminal output
- **[Requests](https://docs.python-requests.org/)**: HTTP requests
- **[otterai](https://github.com/gmchad/otterai-api)**: Unofficial Otter.ai API wrapper

## ⚠️ Important Notes

- Uses the **unofficial Otter.ai API** - may break if Otter.ai changes their internal APIs
- **Rate limited** by default to be respectful to Otter.ai servers
- **Requires valid Otter.ai credentials** - this tool cannot work without a legitimate account
- **No warranty** - this is an unofficial tool for personal use

## 🤝 Contributing

This is a personal project, but improvements are welcome! Please:
- Keep it simple and focused
- Maintain the beautiful CLI experience
- Test thoroughly with small `--max-count` before submitting

## 📜 License

MIT License - Use freely for personal transcript organization.

---

*Built with ❤️ for organizing AI-ready transcripts*
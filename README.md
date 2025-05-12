# Meet2Obsidian

Automated tool for transcribing meeting recordings and integrating them into your Obsidian vault with AI-powered content analysis.

<p align="center">
  <img src="https://img.shields.io/github/license/voftik/meet2obsidian?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square" alt="Python Version">
</p>

## 📝 Description

Meet2Obsidian automatically processes meeting recordings, converts them to text, and creates structured notes in your Obsidian vault. Using AI, it analyzes meeting content to extract key information: main topics, agreements reached, and action items - helping you maintain a comprehensive, searchable archive of your meetings.

## ✨ Key Features

- **Automated Recording Processing**: Monitors for new MP4 files in your designated meetings directory
- **Enhanced Audio Extraction**: Extracts audio from videos in various formats (WAV, MP3, M4A) with quality profiles optimized for speech
- **Speech-to-Text Conversion**: Transcribes speech using Rev.ai's powerful API
- **Structured Notes**: Automatically creates Obsidian notes with sections for:
  - Meeting Information
  - Executive Summary
  - Agreements & Decisions
  - Action Items & Tasks
  - Complete Transcript
- **AI-Powered Content Analysis**: Leverages Claude API to analyze transcripts and extract valuable insights
- **File Management**: Automatically cleans up processed files from your meetings directory
- **Customizable Prompts**: Configure how AI analyzes your meetings with editable prompt templates
- **Secure Storage**: API keys are stored securely using macOS Keychain

## 🔧 How It Works

1. The utility monitors changes in your `/Documents/meet_records/` directory (or custom path)
2. When a new video file is detected:
   - File is validated to ensure it's a proper video file
   - Audio is extracted and saved in your preferred format (WAV, MP3, M4A)
   - Quality profile optimized for speech is applied for better transcription
   - Original video file is removed to save space (optional)
3. Audio file is sent to Rev.ai service for transcription
4. Upon receiving the transcription:
   - Creates "Meeting Records" directory in your Obsidian vault (if not exists)
   - Creates a new note with a name matching the original file
   - Adds the transcription to the "Transcript" section
5. Using Claude API, the tool analyzes the transcript and:
   - Extracts key meeting information
   - Creates an executive summary
   - Identifies agreements and decisions
   - Compiles a list of action items and assigned tasks
6. All processed files are removed from the source directory
7. Optionally links to relevant notes in your vault based on content analysis

## 🚀 Getting Started

### Prerequisites

- macOS system (currently only macOS is supported)
- Python 3.9 or higher
- FFmpeg (installed via Homebrew)
- Obsidian installed on your computer
- Rev.ai account for transcription services
- Anthropic Claude API key for content analysis

### Utility Scripts

Meet2Obsidian includes helpful utility scripts to make your workflow smoother:

- **API Key Setup**: The `scripts/setup_api_keys.py` script helps you securely manage your API keys with testing capabilities
- **Video Validation**: The `scripts/check_videos.py` script checks video files for issues before processing

### Installation

#### Development Installation

```bash
# Clone the repository
git clone https://github.com/voftik/meet2obsidian.git
cd meet2obsidian

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

#### User Installation (Once Released)

```bash
# Install via Homebrew
brew install voftik/tools/meet2obsidian

# Or install via pip
pip install meet2obsidian
```

### Initial Setup

On first launch, Meet2Obsidian will ask for and securely store:
- Path to your Obsidian vault
- Rev.ai API key
- Anthropic Claude API key
- Preferred configuration options

These settings are stored securely in macOS Keychain.

### Usage

```bash
# Start the service
meet2obsidian run

# Check status
meet2obsidian monitor status

# Stop the service
meet2obsidian monitor stop

# Configure settings
meet2obsidian config

# View logs
meet2obsidian logs show

# Process a single file
meet2obsidian process /path/to/meeting.mp4
```

### Running Tests

```bash
# Run all tests
./tests/run_tests.py

# Run processing queue tests
./tests/run_processing_queue_tests.py

# Run specific tests
./tests/run_tests.py tests/unit/test_logging.py

# Alternative method with pytest directly
PYTHONPATH=. pytest tests/
```

## 🔐 Security and Privacy

- API keys are stored securely using macOS Keychain
- All processing happens locally on your machine except for API calls
- No meeting content is stored on external servers beyond necessary API processing
- Temporary files are securely managed and cleaned up after processing

## 🛠️ Advanced Configuration

Meet2Obsidian offers several customization options:

- **Custom Prompts**: Edit AI analysis prompts for different meeting types
- **Templating**: Customize Obsidian note templates
- **Scheduling**: Set up automatic processing at specific times
- **Caching**: Efficient caching system for optimizing API usage and improving performance

## 📋 Future Roadmap

### Recently Completed
- [x] Implementation of structured logging system with JSON formatting and rotation
- [x] Comprehensive testing suite for logging functionality
- [x] CLI commands for log management and viewing
- [x] Implementation of ApplicationManager for process control and monitoring
- [x] LaunchAgent integration for macOS autostart functionality
- [x] Enhanced CLI commands for service management with autostart support

### Coming Soon
- [x] Processing queue system for efficient file handling with features like:
  - Priority-based processing queue for important files
  - Robust error handling with automatic retries
  - State persistence for recovery after application restart
  - Event-based callbacks for processing status updates
- [x] Support for additional audio formats (WAV, MP3, M4A, OGG) with quality profiles
- [x] Robust audio extraction system with advanced error handling and metadata support
- [x] File monitoring implementation with validation for automatic video processing
- [ ] Integration with alternative transcription services
- [ ] Cross-linking between notes based on content context using AI relevance agent
  - Dedicated AI agent evaluates existing vault notes for contextual relevance
  - Creates bidirectional links with related content
  - Builds semantic connections across your knowledge base

## 🔍 Technical Features

### Audio Extraction System
Sophisticated audio extraction capabilities with extensive feature set:
- Support for multiple audio formats (WAV, MP3, M4A, OGG)
- Quality profiles optimized for different use cases (voice, low, medium, high)
- FFmpeg integration for reliable media processing
- Metadata extraction and caching for performance optimization
- Handling of videos without audio tracks by generating silent audio
- Robust validation and error detection for corrupted videos
- Full control over audio parameters (bitrate, sample rate, channels)

### Processing Queue System
Advanced file processing queue with sophisticated features:
- Thread-based concurrent processing for efficient resource utilization
- Priority-based queuing system with configurable priorities
- Robust error handling with automatic retries and failure management
- State persistence for recovery after application restart
- Callback system for processing status monitoring and event handling
- Process cancellation and waiting capabilities
- Comprehensive statistics and state tracking

### File Monitoring System
Automated file detection and processing with:
- Directory watching for new video files
- File validation to ensure proper video format before processing
- Filter capability to match specific file patterns
- Integration with the processing queue
- Maintenance of processed file history

### Local Processing
Audio extraction and file management happen locally, minimizing bandwidth usage.

### Robust Error Handling
The tool automatically recovers from interruptions and API failures, with sophisticated retry logic for transient errors.

### Efficient Resource Usage
Optimized to minimize CPU and memory usage while running in the background, with configurable concurrency limits.

### Structured Logging
Comprehensive logging system with structlog for JSON-formatted logs, log rotation, and contextual logging to simplify troubleshooting and monitoring. Features include:
- Multiple logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log file rotation to manage disk space
- Structured JSON format for machine readability
- Context binding for tracing related log events
- CLI commands for viewing and managing logs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

If you have questions or suggestions, please [create an issue](https://github.com/voftik/meet2obsidian/issues/new) in this repository.

---

<p align="center"><b>Meet2Obsidian</b> — Transforming meetings into structured knowledge.</p>
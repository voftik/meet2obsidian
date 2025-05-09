# Meet2Obsidian

Automated tool for transcribing meeting recordings and integrating them into your Obsidian vault with AI-powered content analysis.

<p align="center">
  <img src="https://img.shields.io/github/license/voftik/meet2obsidian?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square" alt="Python Version">
</p>

## 📝 Description

Meet2Obsidian automatically processes meeting recordings, converts them to text, and creates structured notes in your Obsidian vault. Using AI, it analyzes meeting content to extract key information: main topics, agreements reached, and action items - helping you maintain a comprehensive, searchable archive of your meetings.

## ✨ Key Features

- **Automated Recording Processing**: Monitors for new MP4 files in your designated meetings directory
- **Audio Extraction**: Converts videos to audio format (M4A) while preserving original filenames
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

## 🔧 How It Works

1. The utility monitors changes in your `/Documents/meet_records/` directory (or custom path)
2. When a new MP4 file is detected:
   - Audio is extracted and saved as an M4A file
   - Original MP4 file is removed to save space
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

- Obsidian installed on your computer
- Rev.ai account for transcription services
- Anthropic Claude API key for content analysis

### Installation

```bash
# Clone the repository
git clone https://github.com/voftik/meet2obsidian.git
cd meet2obsidian

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Initial Setup

On first launch, Meet2Obsidian will ask for and securely store:
- Path to your Obsidian vault
- Rev.ai API key
- Anthropic Claude API key
- Preferred configuration options

These settings are stored encrypted in a local configuration file.

## 🔐 Security and Privacy

- API keys are stored securely using environment variables or encrypted configuration
- All processing happens locally on your machine except for API calls
- No meeting content is stored on external servers beyond necessary API processing
- Options to work with locally deployed transcription models for complete privacy

## 🛠️ Advanced Configuration

Meet2Obsidian offers several customization options:

- **Custom Prompts**: Edit AI analysis prompts for different meeting types
- **Templating**: Customize Obsidian note templates
- **Scheduling**: Set up automatic processing at specific times

## 📋 Future Roadmap

- [ ] Support for additional video/audio formats
- [ ] Integration with alternative transcription services
- [ ] Cross-linking between notes based on content context using AI relevance agent
  - Dedicated AI agent evaluates existing vault notes for contextual relevance
  - Creates bidirectional links with related content
  - Builds semantic connections across your knowledge base

## 🔍 Potential Challenges and Solutions

### Handling Large Files
For lengthy recordings, the tool implements chunked processing to manage memory efficiently.

### Transcription Accuracy
For technical discussions or poor audio quality, the tool offers transcript editing capabilities before AI analysis.

### API Rate Limits
Built-in rate limiting and queuing system prevents API throttling during batch processing.

### Meeting Privacy
Option to process sensitive meetings with local models only, though with reduced analysis capabilities.

## 📄 License

This project is licensed under [LICENSE NAME] - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Contact

If you have questions or suggestions, please [create an issue](https://github.com/voftik/meet2obsidian/issues/new) in this repository or contact me directly.

---

<p align="center"><b>Meet2Obsidian</b> — Transforming meetings into structured knowledge.</p>
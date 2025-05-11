# Meet2Obsidian intro
## Project Overview

Meet2Obsidian is a utility that automates the process of transforming video meeting recordings into structured Obsidian notes. The application leverages modern AI tools for speech-to-text conversion and content analysis.

## System Architecture

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  File Monitor     │────▶│  Audio Processor  │────▶│  Transcription    │
│                   │     │                   │     │  Service (Rev.ai) │
└───────────────────┘     └───────────────────┘     └───────────────────┘
                                                              │
                                                              ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  Obsidian         │◀────│  Note Generator   │◀────│  Content Analyzer │
│  Integration      │     │                   │     │  (Claude API)     │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

## Core Components

### 1. File Monitor

**Purpose**: Watches the specified directory for new MP4 files.

**Functionality**:
- Uses a filesystem watcher to detect new files in `/Documents/meet_records/` (configurable path)
- Triggers the processing workflow when new video files are detected
- Implements debouncing to handle large files being copied

**Implementation Details**:
- Uses `watchdog` library for cross-platform file system monitoring
- Maintains a queue of files to be processed sequentially
- Implements logging for monitoring activity

### 2. Audio Processor

**Purpose**: Extracts audio tracks from video files.

**Functionality**:
- Extracts audio track from MP4 to M4A format
- Preserves original filename for continuity
- Handles cleanup of original video files after successful extraction

**Implementation Details**:
- Uses `ffmpeg-python` for audio extraction
- Includes error handling for corrupted video files
- Implements progress tracking for large files

### 3. Transcription Service

**Purpose**: Converts speech to text using Rev.ai API.

**Functionality**:
- Submits audio files to Rev.ai's asynchronous API
- Polls for job completion
- Retrieves and formats transcription results

**Implementation Details**:
- Uses Rev.ai's official Python client
- Implements retry logic for API failures
- Supports fallback to local lightweight models if API is unavailable

### 4. Content Analyzer

**Purpose**: Analyzes transcripts using Claude API to extract structured information.

**Functionality**:
- Processes full transcript through Claude API with specialized prompts
- Extracts key meeting information
- Generates meeting summary
- Identifies agreements and decisions
- Lists action items and tasks

**Implementation Details**:
- Uses Anthropic's Claude API via their Python client
- Configurable prompts for different types of analysis
- Implements token management to handle large transcripts

### 5. Note Generator

**Purpose**: Creates structured Markdown notes from analyzed content.

**Functionality**:
- Assembles content from various analysis components
- Formats according to customizable templates
- Adds metadata (timestamps, participants if available)

**Implementation Details**:
- Uses Jinja2 templating for flexible note formats
- Includes frontmatter generation compatible with Obsidian
- Handles UTF-8 encoding properly

### 6. Obsidian Integration

**Purpose**: Creates or updates notes in the Obsidian vault.

**Functionality**:
- Creates "Meeting Records" directory if needed
- Writes Markdown files to appropriate location
- Ensures proper file permissions

**Implementation Details**:
- Uses standard filesystem operations to create/update files
- Implements locking to prevent concurrent modifications
- Respects Obsidian vault structure

## Configuration System

The application uses a hierarchical configuration system:

1. **Default Configuration**: Hardcoded sensible defaults
2. **User Configuration**: From config file in user's home directory
3. **Command Line Arguments**: Override specific settings for a run

**Configuration Options**:
- Paths (video directory, Obsidian vault location)
- API Keys (stored securely)
- Processing options (cleanup behavior, template preferences)
- Prompt templates for AI analysis

## Data Flow

1. New MP4 file appears in monitored directory
2. System extracts audio track to M4A
3. Original MP4 is removed
4. M4A is sent to Rev.ai for transcription
5. When transcription is complete, text is retrieved
6. Full transcript is analyzed by Claude API with multiple specialized prompts
7. Structured note is generated from analysis results
8. Note is saved to Obsidian vault
9. M4A file is optionally removed

## Security Considerations

- **API Key Storage**: Keys are stored encrypted using OS-specific secure storage
- **Content Privacy**: Analysis happens via API but no permanent storage occurs on third-party servers
- **File Handling**: Temporary files are created in secure directories with appropriate permissions

## Logging System

The application implements a comprehensive logging system to facilitate debugging, monitoring, and auditing:

### Log Levels

- **DEBUG**: Detailed information, typically useful only for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Indication that something unexpected happened, but processing continues
- **ERROR**: Due to a more serious problem, some functionality couldn't be executed
- **CRITICAL**: Serious error indicating that the program itself may be unable to continue running

### Log Categories

Logs are categorized by component for easier filtering:

- `monitor`: File system monitoring events
- `audio`: Audio extraction operations
- `transcribe`: Transcription service interactions
- `analyze`: AI analysis operations
- `note`: Note generation processes
- `obsidian`: Obsidian integration activities
- `security`: Security-related events (authentication, key usage)
- `main`: Application lifecycle events

### Log Format

Each log entry includes:
- Timestamp (ISO format with millisecond precision)
- Log level
- Component identifier
- Process/thread ID
- Message
- Contextual data (when applicable)

Example:
```
2025-05-09T14:23:45.342Z | INFO | monitor | 12345 | New file detected: meeting_2025-05-09.mp4 | {"file_size": 245788672, "mime_type": "video/mp4"}
```

### Log Storage

- Logs are written to rotating files in a dedicated `logs` directory
- Default rotation: 10MB file size, keeping 30 days of history
- Critical events are also stored in a separate high-priority log file
- Configuration options for log verbosity, rotation policy, and storage location

### Processing Status Log

A special JSON-formatted status log tracks the processing state of each file:

```json
{
  "file_id": "20250509_142345_meeting",
  "original_filename": "meeting_2025-05-09.mp4",
  "start_time": "2025-05-09T14:23:45.342Z",
  "stages": [
    {"name": "detection", "status": "completed", "timestamp": "2025-05-09T14:23:45.342Z"},
    {"name": "audio_extraction", "status": "completed", "timestamp": "2025-05-09T14:25:12.125Z"},
    {"name": "video_cleanup", "status": "completed", "timestamp": "2025-05-09T14:25:14.432Z"},
    {"name": "transcription_submit", "status": "completed", "timestamp": "2025-05-09T14:25:20.123Z", "job_id": "rev-12345"},
    {"name": "transcription_complete", "status": "completed", "timestamp": "2025-05-09T14:32:45.632Z"},
    {"name": "ai_analysis", "status": "in_progress", "timestamp": "2025-05-09T14:32:50.125Z"},
    {"name": "note_creation", "status": "pending"},
    {"name": "obsidian_update", "status": "pending"},
    {"name": "cleanup", "status": "pending"}
  ],
  "errors": [],
  "warnings": []
}
```

### Performance Metrics

The logging system also captures performance metrics:
- Processing time for each stage
- API response times
- File sizes and processing rates
- Resource usage (memory, CPU)

### Implementation

- Uses Python's built-in `logging` module with custom formatters and handlers
- Structured logging for machine-readable entries (JSON format)
- Context managers for tracking operation duration and success/failure

## Error Handling

The system implements a comprehensive error handling strategy:

- **Graceful Degradation**: If one component fails, others attempt to continue
- **Retry Logic**: For network-related failures (API calls)
- **Error Classification**: Categorizes errors as transient vs. permanent, and recoverable vs. non-recoverable
- **Recovery Procedures**: Automated recovery procedures for common issues
- **User Notifications**: Clear error messages for fixable issues

## Testing Strategy

1. **Unit Tests**: For core functionality of each component
2. **Integration Tests**: For interaction between components
3. **Mock Testing**: For API interactions
4. **End-to-End Tests**: With sample video files

## Development Environment Setup

1. **Dependencies**:
   - Python 3.8+
   - FFmpeg installed on system path
   - Required Python packages in `requirements.txt`

2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **API Keys**:
   - Rev.ai account and API key
   - Anthropic Claude API key

4. **Configuration**:
   - Copy `config.example.yml` to `config.yml`
   - Update with your API keys and paths

## Project Structure

```
meet2obsidian/
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py
├── config.example.yml
├── meet2obsidian/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration handling
│   ├── monitor.py           # File system monitoring
│   ├── audio.py             # Audio extraction
│   ├── transcribe.py        # Rev.ai integration
│   ├── analyze.py           # Claude API integration
│   ├── note.py              # Note generation
│   ├── obsidian.py          # Obsidian integration
│   ├── security.py          # Secure storage utilities
│   ├── logger.py            # Logging configuration and utilities
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── status_tracker.py # Processing status tracking
│   │   └── metrics.py        # Performance metrics collection
│   └── templates/           # Note templates
│       ├── default.md.j2
│       └── minimal.md.j2
├── logs/                    # Default log directory
│   ├── meet2obsidian.log
│   ├── critical_events.log
│   └── status/              # JSON status logs
└── tests/
    ├── __init__.py
    ├── test_monitor.py
    ├── test_audio.py
    ├── test_transcribe.py
    └── ...
```

## Implementation Roadmap

### Phase 1: Core Functionality
- [x] Repository setup
- [ ] Basic file monitoring
- [ ] Audio extraction from video
- [ ] Integration with Rev.ai API

### Phase 2: Analysis & Note Creation
- [ ] Integration with Claude API
- [ ] Note template system
- [ ] Basic Obsidian integration

### Phase 3: Enhancements
- [ ] Configuration system
- [ ] Improved error handling
- [ ] Logging system
- [ ] Documentation

### Phase 4: Advanced Features
- [ ] AI-powered cross-linking
- [ ] Custom template support
- [ ] CLI interface improvements

## Potential Challenges & Solutions

### Challenge: Processing Large Files
**Solution**: Implement chunked processing, progress tracking, and background processing.

### Challenge: API Rate Limits
**Solution**: Implement queuing, rate limiting, and retries with exponential backoff.

### Challenge: Transcription Accuracy
**Solution**: Provide post-processing options and transcript editing capabilities.

### Challenge: Context Windows with Large Transcripts
**Solution**: Implement intelligent chunking for Claude API to manage token limits.

## Prompt Design for Claude API

Below are the starting points for each prompt. These should be refined based on performance.

### 1. Meeting Information Prompt

```
You are analyzing a meeting transcript. Extract key information about this meeting including:
1. The apparent purpose/type of meeting
2. The main participants (if names are mentioned)
3. The date and time (if mentioned)
4. The main topics discussed

Format your response as neat markdown without additional commentary. Just provide the extracted information.

TRANSCRIPT:
{transcript}
```

### 2. Executive Summary Prompt

```
Create a concise executive summary of the following meeting transcript. Focus on the most important points, decisions, and takeaways. Keep the summary to approximately 200-300 words, formatted as markdown paragraphs without headings.

TRANSCRIPT:
{transcript}
```

### 3. Agreements & Decisions Prompt

```
Extract all agreements and decisions made during this meeting. Include:
1. Clear decisions that were made
2. Commitments that participants agreed to
3. Consensus points reached during discussion

Format as a markdown bullet list, with each agreement as a separate point. If no clear agreements were made, state that.

TRANSCRIPT:
{transcript}
```

### 4. Action Items Prompt

```
Extract all action items, tasks, and follow-ups mentioned in this meeting. For each item, include:
1. The specific task
2. Who is responsible (if mentioned)
3. Deadlines or timeframes (if mentioned)

Format as a markdown checklist using the format:
- [ ] Task description (Owner, Deadline)

If owner or deadline isn't specified, omit that part. If no tasks were assigned, state that.

TRANSCRIPT:
{transcript}
```

## Best Practices for Development

1. **Follow PEP 8** coding style for Python
2. **Document as you code** with docstrings and comments
3. **Write tests alongside code** for new features
4. **Error handling first** - design for failure cases
5. **Secure API keys** - never commit them to the repository
6. **Log appropriately** - informative but not excessive
7. **Commit regularly** with descriptive messages

## Final Notes

This project combines multiple technologies and APIs to create a seamless experience. The most complex aspects will be:

1. Managing the asynchronous nature of the transcription service
2. Handling large files efficiently
3. Designing effective prompts for Claude API
4. Creating a robust error recovery system

By focusing on these aspects and building incrementally, we can develop a powerful tool that transforms meeting recordings into valuable knowledge assets in Obsidian
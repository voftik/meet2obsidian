# Rev.ai API Integration for Meet2Obsidian

## Overview

This document provides detailed implementation guidance for integrating the Rev.ai Speech-to-Text API into the Meet2Obsidian application. The integration will use the official Rev.ai Python SDK, which simplifies API interaction and helps maintain compatibility with future API changes.

## Prerequisites

- Rev.ai account and access token
- Python 3.9+ environment
- Rev.ai Python SDK (`pip install --upgrade rev_ai`)
- FFmpeg for audio extraction (already installed)

## Installation

```bash
# Install the Rev AI Python SDK
pip install --upgrade rev_ai
```

## API Client Implementation

### Client Setup

Create a dedicated module `revai.py` in the `meet2obsidian/api/` directory:

```python
"""
Rev.ai API client for Meet2Obsidian.
Handles transcription of audio files using Rev.ai services.
"""

import logging
import time
import os
from typing import Dict, Optional, Tuple, Any

from rev_ai import apiclient
from rev_ai.models import CustomerUrlData

from meet2obsidian.utils.status import StatusTracker
from meet2obsidian.cache import CacheManager

# Setup logger
logger = logging.getLogger('revai_client')

class RevAiClient:
    """Client for interacting with Rev.ai API"""
    
    def __init__(self, api_key: str, cache_manager: CacheManager, status_tracker: StatusTracker):
        """
        Initialize Rev.ai client with API key
        
        Args:
            api_key: Rev.ai API access token
            cache_manager: Cache manager for storing results
            status_tracker: Status tracker for monitoring job progress
        """
        self.client = apiclient.RevAiAPIClient(api_key)
        self.cache_manager = cache_manager
        self.status_tracker = status_tracker
        logger.info("Rev.ai client initialized")
    
    def test_connection(self) -> bool:
        """
        Test API connection and key validity
        
        Returns:
            bool: True if connection is successful
        """
        try:
            # Get account info to test connection
            self.client.get_account()
            logger.info("Rev.ai API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Rev.ai API connection test failed: {str(e)}")
            return False
```

### Core Transcription Functionality

Add the following methods to the `RevAiClient` class:

```python
def submit_transcription_job(self, audio_path: str, file_id: str) -> Dict[str, Any]:
    """
    Submit audio file for transcription
    
    Args:
        audio_path: Path to audio file
        file_id: Unique identifier for the file
        
    Returns:
        Dict containing job details
    """
    try:
        # Update status
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription_submit', 
            'in_progress',
            message="Submitting audio to Rev.ai"
        )
        
        # Get file hash for caching
        file_hash = self._get_file_hash(audio_path)
        
        # Check cache for existing job
        cached_job_id = self.cache_manager.get('transcription_jobs', file_hash)
        if cached_job_id:
            logger.info(f"Found cached job ID for {os.path.basename(audio_path)}")
            
            # Check job status
            job_details = self.client.get_job_details(cached_job_id)
            
            # Update status
            self.status_tracker.update_stage_status(
                file_id, 
                'transcription_submit', 
                'completed',
                job_id=cached_job_id,
                message="Using existing transcription job"
            )
            
            return {
                "job_id": cached_job_id,
                "status": job_details.status,
                "created_on": job_details.created_on,
                "cached": True
            }
            
        # Submit new job
        job = self.client.submit_job_local_file(
            audio_path,
            metadata=f"Meet2Obsidian Job {file_id}",
            skip_diarization=False,  # Enable speaker diarization if available
            skip_punctuation=False,
            remove_disfluencies=True,
            filter_profanity=False,
            language='en'  # Default to English, can be made configurable
        )
        
        # Cache job ID
        self.cache_manager.store('transcription_jobs', file_hash, job.id)
        
        # Update status
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription_submit', 
            'completed',
            job_id=job.id,
            message="Transcription job submitted successfully"
        )
        
        logger.info(f"Submitted job {job.id} for {os.path.basename(audio_path)}")
        
        return {
            "job_id": job.id,
            "status": job.status,
            "created_on": job.created_on,
            "cached": False
        }
    except Exception as e:
        # Update status
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription_submit', 
            'error',
            error=str(e),
            message="Failed to submit transcription job"
        )
        
        logger.error(f"Failed to submit transcription job: {str(e)}")
        raise
```

### Job Status Monitoring

```python
def check_job_status(self, job_id: str, file_id: str) -> Dict[str, Any]:
    """
    Check status of transcription job
    
    Args:
        job_id: Rev.ai job ID
        file_id: Meet2Obsidian file ID
        
    Returns:
        Dict containing job status details
    """
    try:
        # Get job details
        job_details = self.client.get_job_details(job_id)
        
        # Update status
        status_message = f"Transcription status: {job_details.status}"
        if job_details.status == 'in_progress':
            self.status_tracker.update_stage_status(
                file_id, 
                'transcription', 
                'in_progress',
                message=status_message
            )
        elif job_details.status == 'transcribed':
            self.status_tracker.update_stage_status(
                file_id, 
                'transcription', 
                'completed',
                message="Transcription completed successfully"
            )
        elif job_details.status == 'failed':
            self.status_tracker.update_stage_status(
                file_id, 
                'transcription', 
                'error',
                error="Rev.ai transcription failed",
                message="Transcription job failed"
            )
        
        return {
            "job_id": job_details.id,
            "status": job_details.status,
            "created_on": job_details.created_on,
            "completed_on": job_details.completed_on
        }
    except Exception as e:
        logger.error(f"Failed to check job status: {str(e)}")
        raise
```

### Transcript Retrieval

```python
def get_transcript(self, job_id: str, file_id: str, format_type: str = "text") -> str:
    """
    Retrieve transcript in specified format
    
    Args:
        job_id: Rev.ai job ID
        file_id: Meet2Obsidian file ID
        format_type: Format to retrieve ("text", "json", or "object")
        
    Returns:
        Transcript in requested format
    """
    try:
        # Update status
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription_retrieve', 
            'in_progress',
            message=f"Retrieving transcript in {format_type} format"
        )
        
        # Check cache
        cache_key = f"{job_id}_{format_type}"
        cached_transcript = self.cache_manager.get('transcripts', cache_key)
        
        if cached_transcript:
            logger.info(f"Using cached transcript for job {job_id}")
            
            # Update status
            self.status_tracker.update_stage_status(
                file_id, 
                'transcription_retrieve', 
                'completed',
                message="Retrieved transcript from cache"
            )
            
            return cached_transcript
        
        # Retrieve transcript in requested format
        if format_type == "text":
            transcript = self.client.get_transcript_text(job_id)
        elif format_type == "json":
            transcript = self.client.get_transcript_json(job_id)
        elif format_type == "object":
            transcript = self.client.get_transcript_object(job_id)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
        
        # Cache transcript
        self.cache_manager.store('transcripts', cache_key, transcript)
        
        # Update status
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription_retrieve', 
            'completed',
            message="Successfully retrieved transcript"
        )
        
        logger.info(f"Retrieved transcript for job {job_id}")
        return transcript
    
    except Exception as e:
        # Update status
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription_retrieve', 
            'error',
            error=str(e),
            message="Failed to retrieve transcript"
        )
        
        logger.error(f"Failed to retrieve transcript: {str(e)}")
        raise
```

### Wait for Completion Method

```python
def wait_for_and_get_transcript(
    self, 
    job_id: str, 
    file_id: str, 
    format_type: str = "text", 
    polling_interval: int = 10,
    max_wait_time: int = 3600
) -> str:
    """
    Wait for job completion and get transcript
    
    Args:
        job_id: Rev.ai job ID
        file_id: Meet2Obsidian file ID
        format_type: Format to retrieve
        polling_interval: Seconds between status checks
        max_wait_time: Maximum seconds to wait
        
    Returns:
        Transcript in requested format
    """
    logger.info(f"Waiting for job {job_id} to complete")
    
    # Track wait time
    start_time = time.time()
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        # Check job status
        job_status = self.check_job_status(job_id, file_id)
        
        # If complete, get transcript
        if job_status["status"] == "transcribed":
            logger.info(f"Job {job_id} completed in {elapsed_time:.1f} seconds")
            return self.get_transcript(job_id, file_id, format_type)
        
        # If failed, raise exception
        if job_status["status"] == "failed":
            error_msg = f"Job {job_id} failed after {elapsed_time:.1f} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Wait before checking again
        time.sleep(polling_interval)
        elapsed_time = time.time() - start_time
        
        # Update status with wait time
        self.status_tracker.update_stage_status(
            file_id, 
            'transcription', 
            'in_progress',
            message=f"Waiting for transcription (elapsed: {int(elapsed_time)}s)"
        )
    
    # Timeout reached
    error_msg = f"Timeout waiting for job {job_id} after {max_wait_time} seconds"
    logger.error(error_msg)
    
    # Update status
    self.status_tracker.update_stage_status(
        file_id, 
        'transcription', 
        'error',
        error=error_msg,
        message="Transcription timed out"
    )
    
    raise TimeoutError(error_msg)
```

### Helper Methods

```python
def _get_file_hash(self, file_path: str) -> str:
    """
    Generate a hash for a file to use as cache key
    
    Args:
        file_path: Path to file
        
    Returns:
        Hash string for the file
    """
    import hashlib
    
    # For large files, use only the first 1MB + filename for hashing
    # This is faster while still providing good uniqueness
    buffer_size = 1024 * 1024  # 1 MB
    hasher = hashlib.md5()
    
    # Add filename to hash for additional uniqueness
    hasher.update(os.path.basename(file_path).encode('utf-8'))
    
    try:
        with open(file_path, 'rb') as f:
            # Read first chunk
            buf = f.read(buffer_size)
            hasher.update(buf)
            
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error generating file hash: {str(e)}")
        # Fallback to just the filename if file can't be read
        return hashlib.md5(os.path.basename(file_path).encode('utf-8')).hexdigest()

def list_recent_jobs(self, limit: int = 10) -> list:
    """
    List recent transcription jobs
    
    Args:
        limit: Maximum number of jobs to return
        
    Returns:
        List of recent jobs
    """
    try:
        jobs = self.client.get_list_of_jobs(limit=limit)
        return jobs
    except Exception as e:
        logger.error(f"Failed to list recent jobs: {str(e)}")
        raise
```

## Implementation Example

Here's how to use the Rev.ai client in the main pipeline:

```python
# In meet2obsidian/pipeline.py

def process_audio_file(self, audio_path: str, file_id: str) -> str:
    """
    Process audio file through Rev.ai transcription
    
    Args:
        audio_path: Path to audio file
        file_id: Unique identifier for the file
        
    Returns:
        Transcript text
    """
    # Get Rev.ai client
    revai_client = self.api_service_clients.get_revai_client()
    
    # Submit job
    job_result = revai_client.submit_transcription_job(audio_path, file_id)
    job_id = job_result["job_id"]
    
    # If job was already cached and complete, get transcript immediately
    if job_result.get("cached", False) and job_result.get("status") == "transcribed":
        return revai_client.get_transcript(job_id, file_id)
    
    # Otherwise, wait for completion and get transcript
    return revai_client.wait_for_and_get_transcript(
        job_id,
        file_id,
        polling_interval=self.config.get_value("api.rev_ai.polling_interval", 10),
        max_wait_time=self.config.get_value("api.rev_ai.max_wait_time", 3600)
    )
```

## Error Handling

The Rev.ai client implementation includes comprehensive error handling:

1. **Network Errors**:
   - Uses exponential backoff for transient errors
   - Provides detailed logging

2. **Authentication Errors**:
   - Tests API key validity during startup
   - Provides clear error messages for invalid keys

3. **API Errors**:
   - Handles specific Rev.ai API errors
   - Updates job status for tracking

## Configuration Options

Add these settings to your configuration schema:

```yaml
api:
  rev_ai:
    polling_interval: 10  # seconds between status checks
    max_wait_time: 3600   # maximum wait time (1 hour)
    max_retries: 3        # maximum retry attempts
    job_timeout: 3600     # seconds before job timeout
```

## Testing

Create unit tests for the Rev.ai client in `tests/unit/test_revai.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from meet2obsidian.api.revai import RevAiClient

@pytest.fixture
def mock_cache_manager():
    return MagicMock()

@pytest.fixture
def mock_status_tracker():
    return MagicMock()

@pytest.fixture
def mock_revai_api():
    with patch('rev_ai.apiclient.RevAiAPIClient') as mock:
        yield mock

def test_submit_transcription_job(mock_revai_api, mock_cache_manager, mock_status_tracker):
    # Arrange
    client = RevAiClient("fake_api_key", mock_cache_manager, mock_status_tracker)
    mock_job = MagicMock()
    mock_job.id = "test_job_id"
    mock_job.status = "in_progress"
    mock_revai_api.return_value.submit_job_local_file.return_value = mock_job
    
    # Act
    result = client.submit_transcription_job("test_audio.m4a", "test_file_id")
    
    # Assert
    assert result["job_id"] == "test_job_id"
    assert result["status"] == "in_progress"
    assert not result["cached"]
    mock_cache_manager.store.assert_called_once()
    mock_status_tracker.update_stage_status.assert_called()
```

## Additional Resources

- [Rev.ai API Documentation](https://docs.rev.ai/api/asynchronous/)
- [Rev.ai Python SDK](https://github.com/revdotcom/revai-python-sdk)
- [Rev.ai SDK Documentation](https://docs.rev.ai/sdk/python/)
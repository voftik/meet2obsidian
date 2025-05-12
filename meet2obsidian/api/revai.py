"""
Module for Rev.ai API interactions.

This module provides a client for Rev.ai services with integrated caching
to optimize API usage and improve performance.
"""

import os
import logging
import hashlib
from typing import Optional, Dict, Any, Tuple

# Import necessary for RevAI client - for documentation only, actual import would be:
# import rev_ai

from meet2obsidian.cache import CacheManager
from meet2obsidian.utils.logging import get_logger


class RevAiClient:
    """
    Client for Rev.ai speech-to-text API with caching capabilities.
    
    This client handles interactions with the Rev.ai API for transcribing audio files,
    including submitting transcription jobs, checking job status, and retrieving 
    transcripts. It includes caching to reduce API usage and improve performance.
    """
    
    def __init__(self, api_key: str, cache_manager: Optional[CacheManager] = None, logger=None):
        """
        Initialize the Rev.ai client.
        
        Args:
            api_key: The Rev.ai API key for authentication
            cache_manager: Optional cache manager for caching results
            logger: Optional logger for recording operations
        """
        self.api_key = api_key
        self.logger = logger or get_logger("api.revai")
        
        # Initialize the Rev.ai client - in a real implementation this would be:
        # self._client = rev_ai.client.RevAiClient(self.api_key)
        self._client = None  # Placeholder for the actual Rev.ai client
        
        # Initialize the cache manager
        self._cache_manager = cache_manager or CacheManager(
            os.path.expanduser("~/.cache/meet2obsidian/revai"), 
            retention_days=30,
            logger=self.logger
        )
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Generate a hash for a file to use as a cache key.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Hash string representing the file
        """
        if not os.path.exists(file_path):
            return hashlib.md5(file_path.encode('utf-8')).hexdigest()
            
        # For real files, compute hash based on file path, size and modified time
        file_stat = os.stat(file_path)
        hash_input = f"{file_path}:{file_stat.st_size}:{file_stat.st_mtime}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def submit_job(self, audio_path: str) -> Tuple[str, bool]:
        """
        Submit an audio file for transcription with caching.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Tuple[str, bool]: (job_id, from_cache) where from_cache indicates if result was from cache
        """
        # Generate hash for the file
        file_hash = self._get_file_hash(audio_path)
        
        # Check if job_id is in cache
        job_id = self._cache_manager.get('transcription_jobs', file_hash)
        if job_id:
            self.logger.info(f"Found cached job_id for {audio_path}")
            return job_id, True
            
        # Not in cache, so submit a new job
        # In a real implementation, this would call the Rev.ai API:
        # job = self._client.submit_job_local_file(audio_path)
        # job_id = job.id
        
        # For this example, we'll simulate creating a job ID
        job_id = f"simulated_job_{file_hash[:8]}"
        
        # Store in cache
        self._cache_manager.store('transcription_jobs', file_hash, job_id)
        self.logger.info(f"Submitted new job for {audio_path}, job_id: {job_id}")
        return job_id, False
    
    def get_transcript(self, job_id: str) -> Tuple[str, bool]:
        """
        Get transcript for a job with caching.
        
        Args:
            job_id: The Rev.ai job ID
            
        Returns:
            Tuple[str, bool]: (transcript, from_cache) where from_cache indicates if result was from cache
        """
        # Check if transcript is in cache
        transcript = self._cache_manager.get('transcripts', job_id)
        if transcript:
            self.logger.info(f"Found cached transcript for job {job_id}")
            return transcript, True
            
        # Not in cache, so get from API
        # In a real implementation, this would call the Rev.ai API:
        # transcript = self._client.get_transcript_text(job_id)
        
        # For this example, we'll simulate a transcript
        transcript = f"This is a simulated transcript for job {job_id}."
        
        # Store in cache
        self._cache_manager.store('transcripts', job_id, transcript)
        self.logger.info(f"Retrieved new transcript for job {job_id}")
        return transcript, False
    
    def get_transcript_for_file(self, audio_path: str) -> Tuple[str, bool]:
        """
        Get transcript for an audio file (convenience method with full caching).
        
        This method handles the full process - submitting a job if needed
        and retrieving the transcript, using caching at both steps.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Tuple[str, bool]: (transcript, from_cache) where from_cache indicates if fully cached
        """
        # Check if there's a direct file->transcript cache first
        file_hash = self._get_file_hash(audio_path)
        direct_transcript = self._cache_manager.get('file_transcripts', file_hash)
        if direct_transcript:
            self.logger.info(f"Found direct cached transcript for {audio_path}")
            return direct_transcript, True
        
        # Submit job (may use cache)
        job_id, job_cached = self.submit_job(audio_path)
        
        # Get transcript (may use cache)
        transcript, transcript_cached = self.get_transcript(job_id)
        
        # Store direct file->transcript mapping for faster future access
        self._cache_manager.store('file_transcripts', file_hash, transcript)
        
        # If both steps used cache, we consider it fully cached
        fully_cached = job_cached and transcript_cached
        return transcript, fully_cached
    
    def clear_cache(self) -> Dict[str, int]:
        """
        Clear all Rev.ai API cache.
        
        Returns:
            Dict[str, int]: Dictionary with count of items cleared by type
        """
        results = {}
        results['jobs'] = self._cache_manager.invalidate('transcription_jobs')
        results['transcripts'] = self._cache_manager.invalidate('transcripts')
        results['file_transcripts'] = self._cache_manager.invalidate('file_transcripts')
        results['total'] = sum(results.values())
        
        self.logger.info(f"Cleared Rev.ai cache: {results['total']} items total")
        return results
"""Processing state tracking for meet2obsidian."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json
import os


class ProcessingStatus(Enum):
    """Status of a file in the processing queue."""
    PENDING = "pending"  # File is waiting to be processed
    PROCESSING = "processing"  # File is currently being processed
    COMPLETED = "completed"  # File was successfully processed
    ERROR = "error"  # File encountered an error during processing (may be retried)
    FAILED = "failed"  # File failed processing after all retry attempts


@dataclass
class ProcessingState:
    """State of a file in the processing queue."""
    file_path: str
    status: ProcessingStatus
    priority: int = 0  # Higher number = higher priority
    added_time: datetime = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.added_time is None:
            self.added_time = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "status": self.status.value,
            "priority": self.priority,
            "added_time": self.added_time.isoformat() if self.added_time else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_count": self.error_count,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingState':
        """Create state from dictionary after deserialization."""
        # Convert string dates back to datetime objects
        added_time = datetime.fromisoformat(data["added_time"]) if data.get("added_time") else None
        start_time = datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        
        return cls(
            file_path=data["file_path"],
            status=ProcessingStatus(data["status"]),
            priority=data["priority"],
            added_time=added_time,
            start_time=start_time,
            end_time=end_time,
            error_count=data["error_count"],
            max_retries=data["max_retries"],
            last_error=data["last_error"],
            metadata=data["metadata"]
        )
    
    def mark_processing(self) -> None:
        """Mark file as currently being processed."""
        self.status = ProcessingStatus.PROCESSING
        self.start_time = datetime.now()
    
    def mark_completed(self) -> None:
        """Mark file as successfully processed."""
        self.status = ProcessingStatus.COMPLETED
        self.end_time = datetime.now()
    
    def mark_error(self, error_message: str) -> None:
        """Mark file as having encountered an error during processing."""
        self.status = ProcessingStatus.ERROR
        self.error_count += 1
        self.last_error = error_message
        self.end_time = datetime.now()

        # Mark as failed if max retries reached
        if self.error_count >= self.max_retries:
            self.status = ProcessingStatus.FAILED
            # Don't call mark_failed() as it would increment error_count again
    
    def mark_failed(self) -> None:
        """Mark file as failed after all retry attempts."""
        self.status = ProcessingStatus.FAILED
        self.end_time = datetime.now()
    
    def can_retry(self) -> bool:
        """Check if file can be retried after an error."""
        return self.status == ProcessingStatus.ERROR and self.error_count < self.max_retries
    
    def reset_for_retry(self) -> None:
        """Reset state for retry after an error."""
        if self.can_retry():
            self.status = ProcessingStatus.PENDING
            self.start_time = None
            self.end_time = None
    
    @property
    def is_terminal(self) -> bool:
        """Check if file is in a terminal state (completed or failed)."""
        return self.status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED)
    
    @property
    def processing_time(self) -> Optional[float]:
        """Get the processing time in seconds, if available."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

#!/usr/bin/env python3
"""
Check Videos Script

This script scans one or more directories for video files and checks for common issues:
- Corrupted files
- Zero-length files
- Invalid duration
- Unreadable files or formats

It uses ffprobe/ffmpeg to analyze video files and reports any problems encountered.
"""

import os
import sys
import json
import argparse
import subprocess
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Video extensions to check
VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov', '.mkv', '.avi']

def setup_args() -> argparse.Namespace:
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description='Check video files for potential issues')
    parser.add_argument(
        'paths', 
        metavar='PATH', 
        type=str, 
        nargs='+',
        help='Directories to scan for video files'
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Print verbose information'
    )
    parser.add_argument(
        '--recursive', '-r', 
        action='store_true', 
        help='Recursively scan directories'
    )
    parser.add_argument(
        '--extensions', '-e',
        nargs='+',
        default=VIDEO_EXTENSIONS,
        help=f'Video extensions to check (default: {", ".join(VIDEO_EXTENSIONS)})'
    )
    return parser.parse_args()

def has_ffmpeg() -> bool:
    """Check if ffmpeg and ffprobe are installed."""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ffprobe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        print("Error: ffmpeg and/or ffprobe not found. Please install FFmpeg first.")
        return False

def find_video_files(path: str, extensions: List[str], recursive: bool) -> List[str]:
    """Find all video files in the given directory."""
    video_files = []
    
    if recursive:
        # Use os.walk for recursive search
        for root, _, files in os.walk(path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    video_files.append(os.path.join(root, file))
    else:
        # Non-recursive search
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(file_path)
    
    return video_files

def check_video_file(video_path: str) -> Tuple[bool, str]:
    """
    Check if a video file is valid using ffprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Tuple[bool, str]: (success, error_message)
    """
    # Check if file exists
    if not os.path.exists(video_path):
        return False, f"File does not exist: {video_path}"
    
    # Check if file is readable
    if not os.access(video_path, os.R_OK):
        return False, f"File is not readable: {video_path}"
    
    # Check file size
    file_size = os.path.getsize(video_path)
    if file_size == 0:
        return False, f"File is empty (0 bytes): {video_path}"
    
    # Try to get video duration using ffprobe
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'json', 
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        # Check if duration information is available
        if 'format' not in info or 'duration' not in info['format']:
            return False, f"Unable to determine duration: {video_path}"
        
        duration = float(info['format']['duration'])
        if duration <= 0:
            return False, f"Invalid duration ({duration}s): {video_path}"
        
        # Try to read video frames to check for corruption
        cmd = [
            'ffmpeg',
            '-v', 'error',
            '-i', video_path,
            '-t', '1', # Check only the first second
            '-f', 'null',
            '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 or result.stderr:
            return False, f"Corrupted video file (frame read error): {video_path}\n  Error: {result.stderr.strip()}"
        
        return True, ""
        
    except subprocess.CalledProcessError as e:
        return False, f"Error analyzing video: {video_path}\n  Error: {e.stderr.strip() if hasattr(e, 'stderr') else str(e)}"
    except json.JSONDecodeError:
        return False, f"Invalid ffprobe output (JSON parse error): {video_path}"
    except Exception as e:
        return False, f"Unknown error with video: {video_path}\n  Error: {str(e)}"

def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a video file using ffprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dict containing video information or an empty dict if an error occurred
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, Exception):
        return {}

def format_video_info(info: Dict[str, Any]) -> str:
    """Format video information for display."""
    if not info:
        return "No information available"
    
    format_info = info.get('format', {})
    streams = info.get('streams', [])
    
    # Get duration
    duration_str = "unknown"
    if 'duration' in format_info:
        duration = float(format_info['duration'])
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    # Get video resolution
    video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
    resolution = "unknown"
    if video_stream:
        width = video_stream.get('width', 'unknown')
        height = video_stream.get('height', 'unknown')
        resolution = f"{width}x{height}"
    
    # Get audio info
    audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    audio_info = "No audio"
    if audio_stream:
        audio_codec = audio_stream.get('codec_name', 'unknown')
        audio_channels = audio_stream.get('channels', 'unknown')
        audio_info = f"{audio_codec} ({audio_channels} channels)"
    
    # Format file size
    size_str = "unknown"
    if 'size' in format_info:
        size_bytes = int(format_info['size'])
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
    
    return (
        f"Duration: {duration_str}, "
        f"Size: {size_str}, "
        f"Resolution: {resolution}, "
        f"Format: {format_info.get('format_name', 'unknown')}, "
        f"Audio: {audio_info}"
    )

def main():
    """Main function."""
    args = setup_args()
    
    # Check if ffmpeg is installed
    if not has_ffmpeg():
        sys.exit(1)
    
    # Validate paths
    valid_paths = []
    for path in args.paths:
        if not os.path.exists(path):
            print(f"Error: Path does not exist: {path}")
            continue
        if not os.path.isdir(path):
            print(f"Error: Not a directory: {path}")
            continue
        valid_paths.append(path)
    
    if not valid_paths:
        print("Error: No valid directories provided")
        sys.exit(1)
    
    # Process each path
    all_issues = []
    total_files = 0
    valid_files = 0
    
    for path in valid_paths:
        print(f"\nScanning {path}...")
        video_files = find_video_files(path, args.extensions, args.recursive)
        
        if not video_files:
            print(f"No video files found in {path}")
            continue
        
        print(f"Found {len(video_files)} video files.")
        total_files += len(video_files)
        
        # Check each video file
        for video_path in video_files:
            rel_path = os.path.relpath(video_path, path)
            print(f"Checking: {rel_path}...", end=" ", flush=True)
            
            success, error_message = check_video_file(video_path)
            
            if success:
                print("OK")
                valid_files += 1
                
                if args.verbose:
                    info = get_video_info(video_path)
                    print(f"  {format_video_info(info)}")
            else:
                print("FAILED")
                print(f"  {error_message}")
                all_issues.append((video_path, error_message))
    
    # Print summary
    print("\n" + "="*50)
    print(f"SUMMARY: {total_files} files checked, {valid_files} valid, {len(all_issues)} with issues")
    
    if all_issues:
        print("\nIssues found:")
        for video_path, error in all_issues:
            print(f"- {video_path}")
            print(f"  {error}")
    
    if total_files == valid_files:
        print("\nAll video files are valid!")
        return 0
    else:
        print(f"\n{len(all_issues)} files have issues and may not be processed correctly by meet2obsidian.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
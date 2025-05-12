#!/usr/bin/env python
"""
Script to run audio extractor tests.

This script provides a convenient way to run all tests for the audio extractor
component or specific subsets of tests.
"""

import os
import sys
import argparse
import subprocess
import platform


def check_ffmpeg():
    """Check if FFmpeg is installed and available."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True
        return False
    except FileNotFoundError:
        return False


def run_tests(args):
    """Run the specified tests."""
    # Construct pytest command
    pytest_cmd = ['pytest']
    
    # Add verbosity flag
    if args.verbose:
        pytest_cmd.append('-v')
    
    # Skip slow tests?
    if args.skip_slow:
        pytest_cmd.append('-k')
        pytest_cmd.append('not slow')
    
    # Add test file paths
    if args.integration_only:
        pytest_cmd.append('tests/integration/test_audio_extraction_integration.py')
    elif args.unit_only:
        pytest_cmd.extend([
            'tests/unit/test_audio_extractor.py',
            'tests/unit/test_synthetic_videos.py'
        ])
    else:
        pytest_cmd.extend([
            'tests/unit/test_audio_extractor.py',
            'tests/unit/test_synthetic_videos.py',
            'tests/integration/test_audio_extraction_integration.py'
        ])
    
    # Add any additional pytest arguments
    if args.pytest_args:
        pytest_cmd.extend(args.pytest_args)
    
    # Print command being run
    print(f"Running: {' '.join(pytest_cmd)}")
    
    # Run pytest
    result = subprocess.run(pytest_cmd)
    return result.returncode


def setup_test_environment():
    """Set up the test environment."""
    # Create data directory if it doesn't exist
    os.makedirs('tests/data/videos', exist_ok=True)


def main():
    """Main function - parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run audio extractor tests')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--unit-only', action='store_true', help='Run only unit tests')
    group.add_argument('--integration-only', action='store_true', help='Run only integration tests')
    parser.add_argument('--skip-slow', action='store_true', help='Skip slow tests')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('pytest_args', nargs='*', help='Additional pytest arguments')
    
    args = parser.parse_args()
    
    # Setup testing environment
    setup_test_environment()
    
    # Check for FFmpeg
    if not check_ffmpeg():
        print("WARNING: FFmpeg not found. Some tests will be skipped.")
        print(f"Please install FFmpeg for your platform ({platform.system()}):")
        if platform.system() == 'Linux':
            print("  sudo apt-get install ffmpeg")
        elif platform.system() == 'Darwin':
            print("  brew install ffmpeg")
        elif platform.system() == 'Windows':
            print("  Download from https://ffmpeg.org/download.html or use choco install ffmpeg")
        print()
    
    # Run tests
    return run_tests(args)


if __name__ == '__main__':
    sys.exit(main())
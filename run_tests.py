#!/usr/bin/env python3
"""
Test runner script for meet2obsidian project.

This script provides a convenient way to run different types of tests with various options.
It uses pytest under the hood but provides simplified command-line options.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run tests for meet2obsidian')
    
    # Test selection options
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default if no specific test type is selected)')
    parser.add_argument('--component', type=str, help='Run tests for a specific component (e.g., launchagent, monitor)')
    
    # Test behavior options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--failfast', '-f', action='store_true', help='Stop on first failure')
    parser.add_argument('--coverage', '-c', action='store_true', help='Generate test coverage report')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    
    # Extra pytest arguments
    parser.add_argument('--extra', type=str, help='Extra arguments to pass to pytest (in quotes)', default='')
    
    return parser.parse_args()


def construct_command(args):
    """Construct the pytest command based on arguments."""
    command = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        command.append("-v")
    
    # Add failfast
    if args.failfast:
        command.append("--exitfirst")
    
    # Add coverage if requested
    if args.coverage:
        command.append("--cov=meet2obsidian")
        if args.html:
            command.append("--cov-report=html")
    
    # Filter tests based on type
    if args.unit:
        command.append("tests/unit/")
    elif args.integration:
        command.append("tests/integration/")
    elif args.component:
        component = args.component.lower()
        # Map component names to test paths
        component_map = {
            "launchagent": ["tests/unit/test_launchagent.py", "tests/unit/test_application_manager_launchagent.py",
                          "tests/integration/test_launchagent_integration.py"],
            "monitor": ["tests/unit/test_application_manager.py", "tests/integration/test_file_monitor_integration.py"],
            "config": ["tests/unit/test_config.py"],
            "cli": ["tests/unit/test_cli.py"],
            "security": ["tests/unit/test_security.py", "tests/integration/test_security_integration.py"],
            "logging": ["tests/unit/test_logging.py"]
        }
        
        if component in component_map:
            command.extend(component_map[component])
        else:
            print(f"Warning: Unknown component '{component}'. Available components: {', '.join(component_map.keys())}")
            print("Running all tests instead.")
            command.append("tests/")
    else:
        # Default: run all tests
        command.append("tests/")
    
    # Add any extra arguments
    if args.extra:
        command.extend(args.extra.split())
    
    return command


def run_tests(command):
    """Run the tests with the given command."""
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command)
    return result.returncode


def main():
    """Main entry point."""
    # Get the script directory
    script_dir = Path(__file__).parent.absolute()
    
    # Parse arguments
    args = parse_args()
    
    # Change to script directory to ensure correct paths
    os.chdir(script_dir)
    
    # Ensure Python path includes project root
    sys.path.insert(0, str(script_dir))
    
    # Generate and run the command
    command = construct_command(args)
    return run_tests(command)


if __name__ == "__main__":
    sys.exit(main())
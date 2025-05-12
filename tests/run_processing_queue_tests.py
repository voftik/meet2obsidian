#!/usr/bin/env python
"""Test runner for processing queue system tests."""

import unittest
import os
import sys

# Add the root directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    # Create a test suite with all processing queue tests
    test_suite = unittest.TestSuite()
    
    # Add the unit tests
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName('tests.unit.test_processing_state'))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName('tests.unit.test_processing_queue_add'))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName('tests.unit.test_processing_queue_process'))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName('tests.unit.test_processing_queue_recovery'))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName('tests.unit.test_processing_queue_priority'))
    
    # Add the integration tests
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName('tests.integration.test_processing_queue'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())
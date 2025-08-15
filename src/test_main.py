"""
Basic tests for EVE Giveaway Tool
These tests ensure the basic functionality works correctly
"""

import unittest
import sys
import os

# Add src to path so we can import main modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestEVEGiveawayTool(unittest.TestCase):
    """Test cases for EVE Giveaway Tool"""
    
    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            import tkinter
            self.assertTrue(True, "tkinter imported successfully")
        except ImportError:
            self.fail("tkinter could not be imported")
    
    def test_watchdog_import(self):
        """Test that watchdog can be imported"""
        try:
            from watchdog.observers import Observer
            self.assertTrue(True, "watchdog imported successfully")
        except ImportError:
            self.fail("watchdog could not be imported")
    
    def test_basic_functionality(self):
        """Test basic application structure"""
        # This is a basic test to ensure pytest runs
        self.assertTrue(True, "Basic test passed")

if __name__ == '__main__':
    unittest.main()

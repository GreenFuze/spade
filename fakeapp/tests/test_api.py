#!/usr/bin/env python3
"""
FakeApp API Tests
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.main import app

class TestAPI(unittest.TestCase):
    """Test cases for FakeApp API."""
    
    def setUp(self):
        """Set up test client."""
        self.client = app.test_client()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'fakeapp-api')
    
    def test_version(self):
        """Test version endpoint."""
        response = self.client.get('/api/version')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['version'], '1.0.0')
        self.assertEqual(data['name'], 'FakeApp')

if __name__ == '__main__':
    unittest.main()

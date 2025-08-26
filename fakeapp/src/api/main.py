#!/usr/bin/env python3
"""
FakeApp API - Sample API implementation
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "fakeapp-api"})

@app.route('/api/version')
def version():
    """Version endpoint."""
    return jsonify({"version": "1.0.0", "name": "FakeApp"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

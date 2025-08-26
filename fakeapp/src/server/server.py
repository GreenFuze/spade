#!/usr/bin/env python3
"""
FakeApp Server - Sample server implementation
"""

import asyncio
import json
from aiohttp import web

async def handle_health(request):
    """Health check handler."""
    return web.json_response({
        "status": "healthy",
        "service": "fakeapp-server"
    })

async def handle_metrics(request):
    """Metrics handler."""
    return web.json_response({
        "requests": 100,
        "errors": 0,
        "uptime": "2h 30m"
    })

def create_app():
    """Create the web application."""
    app = web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/metrics', handle_metrics)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)

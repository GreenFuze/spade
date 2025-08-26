# FakeApp API Documentation

## Overview

FakeApp provides a RESTful API for testing SPADE workspace initialization and configuration management.

## Endpoints

### Health Check

**GET** `/api/health`

Returns the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "service": "fakeapp-api"
}
```

### Version

**GET** `/api/version`

Returns the current version information.

**Response:**
```json
{
  "version": "1.0.0",
  "name": "FakeApp"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK` - Success
- `404 Not Found` - Endpoint not found
- `500 Internal Server Error` - Server error

## Testing

Run the test suite with:
```bash
python -m pytest tests/
```

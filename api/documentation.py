"""
API Documentation

This module provides comprehensive documentation for the URL Shortener API.

## Authentication

All API endpoints (except public ones) require authentication using Token Authentication.

### Getting a Token
POST /api/auth/token/
{
    "username": "your_email@example.com",
    "password": "your_password"
}

Response:
{
    "token": "your_auth_token",
    "user_id": 1,
    "email": "your_email@example.com",
    "is_premium": false
}

### Using the Token
Include the token in the Authorization header:
Authorization: Token your_auth_token

## Endpoints

### URL Management

#### List/Create URLs
GET /api/urls/
- Query parameters: is_active, is_public, search, page, page_size
- Returns paginated list of user's URLs

POST /api/urls/
{
    "original_url": "https://example.com",
    "custom_alias": "my-link",  // optional
    "is_public": true,          // optional, default: true
    "expires_at": "2024-12-31T23:59:59Z"  // optional
}

#### URL Details
GET /api/urls/{id}/
PUT /api/urls/{id}/
DELETE /api/urls/{id}/

#### URL Analytics
GET /api/urls/{id}/analytics/?days=30
- Returns comprehensive analytics for the URL

#### URL Clicks
GET /api/urls/{id}/clicks/
- Returns paginated list of clicks for the URL

#### QR Code
GET /api/urls/{id}/qr/
- Returns QR code information for the URL

### Bulk Operations

#### Bulk Create URLs
POST /api/urls/bulk-create/
{
    "urls": ["https://example1.com", "https://example2.com"],
    "is_public": true,
    "expires_at": "2024-12-31T23:59:59Z"
}

#### Bulk Delete URLs
DELETE /api/urls/bulk-delete/
{
    "url_ids": [1, 2, 3]
}

### User Data

#### User Statistics
GET /api/user/stats/
- Returns user's overall statistics

#### User Profile
GET /api/user/profile/
- Returns user profile information

### Public Endpoints

#### Public URL Info
GET /api/public/{short_code}/
- Returns public information about a short URL (no auth required)

## Rate Limits

- Free users: 100 requests/hour, 20 URLs/day
- Premium users: 1000 requests/hour, unlimited URLs

## Error Responses

All errors follow this format:
{
    "error": true,
    "message": "Error description",
    "details": {...}
}

Common HTTP status codes:
- 400: Bad Request (invalid data)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error
"""

API_EXAMPLES = {
    "create_url": {
        "request": {
            "method": "POST",
            "url": "/api/urls/",
            "headers": {
                "Authorization": "Token your_auth_token",
                "Content-Type": "application/json"
            },
            "body": {
                "original_url": "https://www.example.com/very/long/url/path",
                "custom_alias": "my-example",
                "is_public": True
            }
        },
        "response": {
            "id": 1,
            "original_url": "https://www.example.com/very/long/url/path",
            "short_code": "my-example",
            "short_url": "http://127.0.0.1:8000/my-example",
            "is_active": True,
            "is_public": True,
            "expires_at": None,
            "click_count": 0,
            "unique_clicks": 0,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
    },
    "get_analytics": {
        "request": {
            "method": "GET",
            "url": "/api/urls/1/analytics/?days=7",
            "headers": {
                "Authorization": "Token your_auth_token"
            }
        },
        "response": {
            "total_clicks": 150,
            "unique_clicks": 75,
            "clicks_today": 12,
            "clicks_this_week": 89,
            "clicks_this_month": 150,
            "top_countries": [
                {"country": "United States", "count": 45},
                {"country": "Canada", "count": 20}
            ],
            "top_browsers": [
                {"browser": "Chrome 120.0", "count": 80},
                {"browser": "Firefox 121.0", "count": 35}
            ],
            "daily_clicks": [
                {"date": "2024-01-01", "clicks": 20},
                {"date": "2024-01-02", "clicks": 15}
            ]
        }
    }
}

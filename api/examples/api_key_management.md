# API Key Management Portal - Usage Examples

This document provides examples of how to use the API key management endpoints.

## Prerequisites

- Email address for authentication
- Access to email for magic link
- Base URL: `http://localhost:8000` (or your deployed API URL)

## Authentication Flow

### Step 1: Request Magic Link Login

Request a magic link to be sent to your email:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your.email@example.com"}'
```

Response:
```json
{
  "message": "Magic link sent to your email",
  "email": "your.email@example.com"
}
```

### Step 2: Verify Magic Link Token

After clicking the magic link in your email, extract the token and verify it:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify" \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_FROM_EMAIL"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "abc123def456...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Save the `access_token` and `refresh_token` - you'll need them for subsequent requests!**

### Step 3: Refresh Access Token (Optional)

When your access token expires (after 1 hour), refresh it:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "X-Refresh-Token: YOUR_REFRESH_TOKEN"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## API Key Management

All API key management endpoints require authentication via the access token obtained from the authentication flow above.

### Register a New API Key

Create a new API key for using the classification endpoints:

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys/register" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"label": "Production API"}'
```

Response:
```json
{
  "api_key": "pk_live_abc123def456...",
  "api_key_id": "key_xyz789",
  "created_at": "2024-01-01T10:00:00Z",
  "label": "Production API"
}
```

**⚠️ IMPORTANT: Save the `api_key` value immediately! It is only shown once and cannot be retrieved later.**

### List Your API Keys

View all your API keys (active and revoked):

```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/list" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "keys": [
    {
      "api_key_id": "key_xyz789",
      "label": "Production API",
      "status": "active",
      "created_at": "2024-01-01T10:00:00Z",
      "last_used_at": "2024-01-05T14:30:00Z",
      "tier": "free"
    },
    {
      "api_key_id": "key_old456",
      "label": "Development API",
      "status": "revoked",
      "created_at": "2023-12-01T10:00:00Z",
      "last_used_at": "2024-01-01T09:00:00Z",
      "tier": "free"
    }
  ],
  "total": 2
}
```

### Rotate an API Key

Replace an existing API key with a new one (old key is immediately revoked):

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys/rotate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key_id": "key_xyz789"}'
```

Response:
```json
{
  "api_key": "pk_live_new789xyz...",
  "api_key_id": "key_new123",
  "created_at": "2024-01-05T15:00:00Z",
  "label": "Production API (Rotated)"
}
```

**⚠️ IMPORTANT: The old key is immediately revoked and the new key is active. Update your applications immediately!**

### Revoke an API Key

Permanently deactivate an API key:

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys/revoke" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key_id": "key_xyz789"}'
```

Response:
```json
{
  "revoked": true,
  "api_key_id": "key_xyz789"
}
```

**⚠️ WARNING: This action cannot be undone. The key will be permanently deactivated within 5 minutes system-wide.**

## Using Your API Key

Once you have an API key, you can use it to access the classification endpoints:

```bash
curl -X POST "http://localhost:8000/api/v1/classify" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": [
      {
        "id": "protein1",
        "sequence": "MKVLWAASLLLLASAARA"
      }
    ]
  }'
```

## Rate Limits (Free Tier)

- **1,000 sequences per day**
- **100 requests per minute**
- **Up to 50 sequences per batch**

## Security Best Practices

1. **Never commit API keys to version control**
2. **Store API keys in environment variables or secure vaults**
3. **Rotate keys regularly (every 90 days recommended)**
4. **Use different keys for development and production**
5. **Revoke keys immediately if compromised**
6. **Monitor key usage via the list endpoint**

## Troubleshooting

### "Invalid API key" Error

- Ensure you're using the correct API key
- Check if the key has been revoked
- Verify the key hasn't expired

### "Invalid or expired access token" Error

- Access tokens expire after 1 hour
- Use the refresh endpoint to get a new access token
- Or login again to get a new set of tokens

### "Missing authorization header" Error

- Ensure you're including the `Authorization: Bearer YOUR_ACCESS_TOKEN` header
- Check for typos in the header name

### "Rate limit exceeded" Error

- You've hit your daily or per-minute limit
- Wait for the limit to reset
- Consider upgrading to a premium tier (contact support)

## Support

For questions or issues, please:
- Check the interactive API documentation at `/docs`
- Review the main README
- Open an issue on GitHub

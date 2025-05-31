# Security Setup Guide

This guide covers the complete security implementation for your Personal RAG Server, including authentication, authorization, rate limiting, and secure configuration.

## 🔐 Security Features Implemented

### Authentication & Authorization

-   **JWT Token Authentication** - Secure, stateless authentication
-   **API Key Authentication** - For service-to-service communication
-   **Role-Based Access Control (RBAC)** - Admin, User, Guest, Service roles
-   **Permission-Based Authorization** - Granular permissions for different operations

### Security Middleware

-   **Rate Limiting** - Prevent abuse and DoS attacks
-   **CORS Configuration** - Secure cross-origin resource sharing
-   **Security Headers** - Comprehensive security headers (HSTS, CSP, etc.)
-   **Request ID Tracking** - For audit logging and debugging

### Password Security

-   **BCrypt Hashing** - Industry-standard password hashing
-   **Password Strength Validation** - Configurable password policies
-   **Password Expiration** - Optional password aging

## 🚀 Quick Setup

### 1. Install Security Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Environment Configuration

Create a `.env` file in your project root:

```bash
# Copy and modify this configuration

# =================
# REQUIRED SETTINGS
# =================

# IMPORTANT: Generate a strong secret key!
SECRET_KEY=your-super-secret-key-change-this-in-production

# First Admin User (change these!)
FIRST_SUPERUSER_USERNAME=admin
FIRST_SUPERUSER_EMAIL=admin@yourdomain.com
FIRST_SUPERUSER_PASSWORD=changeme123

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=rag_server

# Vector Database (Pinecone)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=rag-server

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key

# =================
# OPTIONAL SETTINGS
# =================

# Environment
ENVIRONMENT=development
DEBUG=true

# JWT Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (adjust for your frontend)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### 3. Generate a Secure Secret Key

Use one of these methods to generate a secure secret key:

```bash
# Method 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using OpenSSL
openssl rand -base64 32

# Method 3: Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### 4. Start the Server

```bash
python -m app.main
```

The server will automatically:

-   Create the first superuser account
-   Set up all security middleware
-   Initialize the database connections

## 🔑 Authentication Methods

### JWT Token Authentication

1. **Login to get a token:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"
```

2. **Use the token in subsequent requests:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/auth/me"
```

### API Key Authentication

1. **Create an API key:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "permissions": ["read:documents", "write:conversations"]
  }'
```

2. **Use the API key:**

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/assistants"
```

## 👥 User Management

### User Roles & Permissions

| Role        | Permissions                                              |
| ----------- | -------------------------------------------------------- |
| **Admin**   | All permissions including user management                |
| **User**    | Read/write documents, conversations, categories          |
| **Guest**   | Read-only access to documents, conversations, categories |
| **Service** | API access for automated systems                         |

### Creating Users

**Via API (Admin only):**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/users" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecurePass123",
    "role": "user"
  }'
```

**Via Registration (if enabled):**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

## 🛡️ Security Configuration

### Password Policies

Configure password requirements in your `.env`:

```bash
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=false
```

### Rate Limiting

Configure rate limiting to prevent abuse:

```bash
RATE_LIMIT_REQUESTS=100    # Requests per period
RATE_LIMIT_PERIOD=60       # Period in seconds
RATE_LIMIT_BURST=10        # Burst allowance
```

### CORS Configuration

For production, specify exact origins:

```bash
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## 🏭 Production Deployment

### 1. Environment Configuration

```bash
# Production settings
ENVIRONMENT=production
DEBUG=false

# Use a strong, random secret key
SECRET_KEY=your-production-secret-key-32-chars-minimum

# Secure CORS origins
BACKEND_CORS_ORIGINS=https://yourdomain.com

# Production database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/rag_server

# SSL/Security settings
ENABLE_SECURITY_HEADERS=true
```

### 2. Security Headers

The application automatically adds these security headers in production:

-   `X-Content-Type-Options: nosniff`
-   `X-Frame-Options: DENY`
-   `X-XSS-Protection: 1; mode=block`
-   `Strict-Transport-Security: max-age=31536000; includeSubDomains`
-   `Referrer-Policy: strict-origin-when-cross-origin`
-   `Content-Security-Policy: default-src 'self'`

### 3. Reverse Proxy (Nginx Example)

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔍 Monitoring & Auditing

### Health Checks

Monitor your application:

```bash
# Basic health check
curl "http://localhost:8000/health"

# System status (admin only)
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/auth/system/status"
```

### Request Logging

All requests are automatically logged with:

-   Request method and path
-   Response status code
-   Processing time
-   Unique request ID

### User Activity

Monitor user activity through:

-   Login timestamps
-   Login counts
-   API key usage tracking
-   Permission-based access logs

## 🚨 Security Best Practices

### 1. Secret Management

-   Never commit secrets to version control
-   Use environment variables or secret management services
-   Rotate secrets regularly

### 2. Database Security

-   Use connection encryption (SSL/TLS)
-   Implement network-level access controls
-   Regular security updates

### 3. API Security

-   Always use HTTPS in production
-   Implement proper rate limiting
-   Validate and sanitize all inputs
-   Use least-privilege principle for permissions

### 4. Monitoring

-   Monitor for suspicious activity
-   Set up alerts for failed authentication attempts
-   Regular security audits

## 🔧 Troubleshooting

### Common Issues

**Authentication Errors:**

```bash
# Check if user exists and is active
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/auth/users"

# Validate password requirements
curl -X POST "http://localhost:8000/api/v1/auth/validate-password" \
  -H "Content-Type: application/json" \
  -d '{"password": "testpassword"}'
```

**Permission Errors:**

-   Check user role and permissions
-   Verify JWT token hasn't expired
-   Ensure API key has correct permissions

**Rate Limiting:**

-   Check rate limit headers in response
-   Implement exponential backoff in client
-   Consider increasing limits for legitimate high-volume use

## 📚 API Reference

### Authentication Endpoints

-   `POST /api/v1/auth/login` - User login
-   `POST /api/v1/auth/register` - User registration
-   `GET /api/v1/auth/me` - Current user info
-   `PUT /api/v1/auth/me` - Update current user

### User Management (Admin)

-   `GET /api/v1/auth/users` - List users
-   `POST /api/v1/auth/users` - Create user
-   `GET /api/v1/auth/users/{id}` - Get user
-   `PUT /api/v1/auth/users/{id}` - Update user
-   `DELETE /api/v1/auth/users/{id}` - Delete user

### API Key Management

-   `POST /api/v1/auth/api-keys` - Create API key
-   `GET /api/v1/auth/api-keys` - List my API keys
-   `DELETE /api/v1/auth/api-keys/{id}` - Delete API key
-   `PATCH /api/v1/auth/api-keys/{id}/revoke` - Revoke API key

For complete API documentation, visit `/docs` when running in development mode.

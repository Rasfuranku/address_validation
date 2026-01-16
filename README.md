# Address Validation Service

A Python microservice for validating and standardizing US property addresses. It acts as an API Gateway/Proxy to the **Smarty** (formerly SmartyStreets) API, enhancing it with caching, input normalization, rate limiting, and standardized error handling.

## 🚀 Features

*   **Robust Architecture:** Built with FastAPI, adhering to Enterprise Standards (API Versioning, Router Decomposition).
*   **Smart Caching:** Redis-based caching with intelligent key generation (token sorting) to handle scrambled inputs (e.g., "123 Main St 90210" vs "90210 123 Main St").
*   **Input Pipeline:** Sanitizes, validates, and normalizes address strings before they reach the provider.
*   **Global Quota:** Enforces a daily limit (default: 33 requests) to prevent API overage charges.
*   **Security:** API Key authentication using hashed keys (Zero-Knowledge storage).
*   **Resilience:** Fail-open caching and standardized error responses.
*   **Observability:** Structured logging (JSON-ready format).

## 🛠️ Tech Stack

*   **Framework:** FastAPI
*   **Server:** Uvicorn
*   **Language:** Python 3.11+
*   **Package Manager:** `uv`
*   **Cache:** Redis
*   **Validation:** Pydantic v2
*   **Testing:** Pytest, Pytest-Cov, Asyncio
*   **Provider:** Smarty -> Used instead of the USPS API as it is free, focused on US addresses. Additionaly USPS asked for a US phone number for verification, so this was just simple to set up.

## ⚡ Getting Started

### 1. Prerequisites
*   Docker & Docker Compose (Recommended)
*   OR Python 3.11+ and [uv](https://github.com/astral-sh/uv) installed locally.

### 2. Configuration
Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` and set your Smarty credentials:
```ini
SMARTY_AUTH_ID=your_auth_id
SMARTY_AUTH_TOKEN=your_auth_token
SMARTY_DAILY_LIMIT=33
REDIS_URL=redis://redis:6379/0  # For Docker
# REDIS_URL=redis://localhost:6379/0 # For Local run
```

### 3. Running with Docker (Recommended)

Build and start the services:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### 4. Running Locally

1.  **Install dependencies:**
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e ".[dev]"
    ```
2.  **Start Redis:** (Ensure you have a local Redis instance running)
3.  **Run the server:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

## 🔐 Authentication

The service requires an **API Key** passed in the `X-API-Key` header. Keys are hashed before storage.

### Generating a Key
Use the included utility script to generate a secure key and register its hash in Redis.

**Run this command (locally or inside the container):**

```bash
# Locally
uv run scripts/manage_keys.py --add

# Or inside Docker
docker-compose exec app python scripts/manage_keys.py --add
```

*   **Output:** The script will display a **Raw Key**. Save this immediately; it is never stored.
*   The **Hash** is automatically added to Redis.

## 📡 API Usage

**Base URL:** `http://localhost:8000/v1`

### 1. Health Check
*   **Endpoint:** `GET /health` (Root) or `GET /v1/health`
*   **Response:** `{"status": "ok"}`

### 2. Validate Address
*   **Endpoint:** `POST /v1/validate-address`
*   **Headers:**
    *   `X-API-Key`: `<YOUR_RAW_KEY>`
    *   `Content-Type`: `application/json`
*   **Body:**
    ```json
    {
      "address_raw": "07055 130 jackson st"
    }
    ```

**Example cURL:**

```bash
curl --location 'http://localhost:8000/v1/validate-address' \
--header 'X-API-Key: addr_vk_YourKeyHere...' \
--header 'Content-Type: application/json' \
--data '{
    "address_raw": "07055 130 jackson st"
}'
```

### Response Format
All responses follow a standardized schema:

**Success:**

```json
{
  "success": true,
  "data": {
    "address_raw": "...",
    "standardized": {
      "street": "130 Jackson St",
      "city": "East Rutherford",
      "state": "NJ",
      "zip_code": "07055-5202"
    },
    "valid": true
  },
  "error": null
}
```

**Error:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": 429,
    "message": "Daily validation quota exceeded.",
    "type": "quota_exceeded"
  }
}
```

## 🧪 Testing

Run the comprehensive test suite using `pytest`:

```bash
uv run pytest
```

Tests cover:
*   Unit tests for logic (Input Processing, Key Generation).
*   Integration tests for API endpoints.
*   Mocked external calls (Smarty, Redis) for resilience testing.

## 📂 Project Structure

```
app/
├── api/
│   └── v1/
│       ├── endpoints/   # Route handlers (address.py, health.py)
│       └── router.py    # Router aggregator
├── core/                # Config, Security, Logging, Exceptions
├── interfaces/          # Abstract Base Classes (Validator)
├── schemas/             # Pydantic Models (Request/Response)
├── services/            # Business Logic (Cache, Input, Validation)
└── main.py              # App entry point
scripts/
└── manage_keys.py       # API Key management utility
tests/                   # Pytest suite
```

# ✨ USE OF AI

There were mainly 11 heavy interactions with Gemini Pro. I can share the prompts used per request.
The prompts follow the same structure as stated below:

```
### Description of the task
Brief description of the problem and the role to execute, Sr Software engineer, QA engineer, etc...

### Context
Brief description of the task and current state of the project.

# Requirements
A list of requirements, usually enumerated from 1 to 6.
Step number 6 always refers to testing, using TDD.

# Deliverables
A short list of what to expect as a successful task.
```

### System Design - Prompting engineering

1. Project setup, Docker, Redis, TDD methodology, and libraries to use. API Gateway/Proxy pattern, Adapter Pattern for provider implementation
2. Input processing pipeline, initial sanitization, validation, and normalization,
3. Suite Test for provider Smarty, focused on valid/invalid addresses, typos, API failure, and different input text formats.
4. Redis Cache Layer set up, connection management, Resilience, serialization, basic TTL expiration set to 30 days, smart key generation.
5. API Authentication Strategy, header-based mechanism, security architecture, hashing (SHA-256), timing attack protection, and management script.
6. API Rate limit Token, 33 by default, as Smarty is 1k per month.
7. Logging, setup, refactoring, and replacing prints
8. Error Handling, standarized response schema, custom exception hierarchy (AddresProviderError, ProviderTimeoutError, etc…), Interface pattern.
9. Fixing and improving project structure, API versioning, router decomposition, refactoring routes, cleaning up, and strict typing.
10. Fuzzy matching logic using rapidfuzz, defines a ratio to mark the address with the right status.
# Address Validation Service

A Python microservice for validating and standardizing US property addresses using the API Gateway/Proxy pattern.

## Tech Stack
- **Framework:** FastAPI
- **Web Server:** Uvicorn
- **Package Manager:** `uv`
- **Database/Cache:** Redis
- **Validation:** Pydantic
- **Testing:** Pytest, Pytest-cov
- **Linting/Formatting:** Ruff, Black

## Features
- **Adapter Pattern:** Pluggable provider system (starting with Smarty).
- **Caching:** Redis integration for optimized response times.
- **TDD:** Built following Test-Driven Development principles.
- **Validation:** Standardizes and validates US addresses from free-text input.

## Getting Started

### Prerequisites
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) installed
- Docker and Docker Compose (optional, for containerized execution)

### Local Development Setup

1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```
3. **Run Tests:**
   ```bash
   uv run pytest
   ```

### Running with Docker

1. **Start the services:**
   ```bash
   docker-compose up --build
   ```
2. **Access the API:**
   - API: `http://localhost:8000`
   - Documentation (Swagger): `http://localhost:8000/docs`

## API Endpoints

### Health Check
- **URL:** `/health`
- **Method:** `GET`
- **Response:** `{"status": "ok"}`

### Validate Address
- **URL:** `/validate-address`
- **Method:** `POST`
- **Payload:**
  ```json
  {
    "address_raw": "123 Main St, Anytown, USA"
  }
  ```

## Authentication

The service uses an API Key mechanism (`X-API-Key` header) to authenticate clients.

### Managing Keys
Use the provided utility script to generate and register keys:

1.  **Generate and Add a Key:**
    ```bash
    python scripts/manage_keys.py --add
    ```
    *   Saves the **Raw Key** securely.
    *   Adds the **Key Hash** to Redis.

2.  **Generate Only (Manual Add):**
    ```bash
    python scripts/manage_keys.py
    ```

### Using the API
Include the header in your requests:
```http
X-API-Key: addr_vk_your_generated_key_here
```

### Swagger UI
The interactive documentation (`/docs`) supports API Key authorization. Click the "Authorize" button and enter your raw API Key.

## Project Structure
- `app/api/`: API route definitions.
- `app/core/`: Configuration and dependencies.
- `app/services/`: Business logic and external providers.
- `app/schemas.py`: Pydantic models.
- `tests/`: Unit and integration tests.

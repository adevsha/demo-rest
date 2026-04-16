# demo-rest

A simple REST API built with FastAPI and Python, using in-memory data storage. Provides CRUD endpoints for users, products, and orders with JWT authentication.

## Tech Stack

- **Python 3.12+**
- **FastAPI** - web framework
- **Uvicorn** - ASGI server
- **uv** - package manager
- **PyJWT** - JWT token handling
- **bcrypt** - password hashing
- **Docker** - containerization

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── dependencies.py      # Auth dependency (get_current_user)
├── models/              # Pydantic data models
│   ├── auth.py          # LoginRequest, TokenResponse
│   ├── user.py          # User schemas (create, update, response)
│   ├── product.py       # Product schemas (create, update, response)
│   └── order.py         # Order schemas (create, response with resolved details)
├── data/
│   └── store.py         # In-memory data store + password helpers
├── controllers/         # Business logic (CRUD operations)
│   ├── auth.py          # Authentication + JWT token management
│   ├── user.py
│   ├── product.py
│   └── order.py
└── routes/              # API endpoint definitions
    ├── health.py
    ├── auth.py
    ├── user.py
    ├── product.py
    └── order.py
```

## API Endpoints

### Public

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/login` | Login and get JWT token |

### Protected (require `Authorization: Bearer <token>`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/` | Create a user |
| GET | `/users/` | List all users |
| GET | `/users/{user_id}` | Get a user by ID |
| PATCH | `/users/{user_id}` | Update a user |
| DELETE | `/users/{user_id}` | Delete a user |
| POST | `/products/` | Create a product |
| GET | `/products/` | List all products |
| GET | `/products/{product_id}` | Get a product by ID |
| PATCH | `/products/{product_id}` | Update a product |
| DELETE | `/products/{product_id}` | Delete a product |
| POST | `/orders/` | Create an order (chains auth user + products) |
| GET | `/orders/` | List all orders (resolves user and product details) |
| GET | `/orders/{order_id}` | Get an order by ID |
| DELETE | `/orders/{order_id}` | Delete an order |

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed
- Python 3.12 or higher
- Docker (optional, for containerized usage)

### Run Locally

```bash
# Install dependencies
uv sync

# Start the development server
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Run with Docker

```bash
# Build the image
docker build -t demo-rest .

# Run the container
docker run -p 8000:8000 demo-rest
```

## Usage Examples

### Authentication

All dummy users share the password `password123`. Login to get a JWT token:

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

Use the token in subsequent requests:

```bash
TOKEN="<paste your access_token here>"

# List all users
curl http://localhost:8000/users/ \
  -H "Authorization: Bearer $TOKEN"

# List all products
curl http://localhost:8000/products/ \
  -H "Authorization: Bearer $TOKEN"
```

### Orders (chained endpoint)

Orders link users and products. Creating an order uses the authenticated user and validates product IDs. Fetching an order resolves user names and product details.

```bash
# Create an order (user comes from your JWT token)
curl -X POST http://localhost:8000/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 1}, {"product_id": 9, "quantity": 3}]}'

# List all orders (includes resolved user_name and product details)
curl http://localhost:8000/orders/ \
  -H "Authorization: Bearer $TOKEN"
```

### CRUD Operations

```bash
# Create a user
curl -X POST http://localhost:8000/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe", "email": "jane@example.com", "age": 28, "password": "secret"}'

# Update a user
curl -X PATCH http://localhost:8000/users/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated"}'

# Delete a user
curl -X DELETE http://localhost:8000/users/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive Docs

FastAPI provides auto-generated interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Use the lock icon in Swagger UI to enter your Bearer token for authenticated requests.

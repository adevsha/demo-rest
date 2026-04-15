# demo-rest

A simple REST API built with FastAPI and Python, using in-memory data storage. Provides CRUD endpoints for users and products resources.

## Tech Stack

- **Python 3.12+**
- **FastAPI** - web framework
- **Uvicorn** - ASGI server
- **uv** - package manager
- **Docker** - containerization

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── models/              # Pydantic data models
│   ├── user.py          # User schemas (create, update, response)
│   └── product.py       # Product schemas (create, update, response)
├── data/
│   └── store.py         # In-memory data store (10 users, 10 products)
├── controllers/         # Business logic (CRUD operations)
│   ├── user.py
│   └── product.py
└── routes/              # API endpoint definitions
    ├── health.py
    ├── user.py
    └── product.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
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

```bash
# Health check
curl http://localhost:8000/health

# List all users
curl http://localhost:8000/users/

# Get a single user
curl http://localhost:8000/users/1

# Create a user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe", "email": "jane@example.com", "age": 28}'

# Update a user
curl -X PATCH http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated"}'

# Delete a user
curl -X DELETE http://localhost:8000/users/1
```

## Interactive Docs

FastAPI provides auto-generated interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

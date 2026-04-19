# demo-rest

A small REST API that shows how one service can tie together three different backends: a SQL database (MySQL) for people and things, a document store (MongoDB) for orders, and a message bus (Kafka) for change events. It's intentionally small so you can read the whole thing in an afternoon, but it's wired end-to-end the way a real service would be.

It's useful as a teaching sample, as a target for integration tests, and as a starting point for your own experiments.

---

## Table of contents

1. [What you'll see](#1-what-youll-see)
2. [How the pieces fit together](#2-how-the-pieces-fit-together)
3. [Quick start (5 minutes)](#3-quick-start-5-minutes)
4. [First walkthrough](#4-first-walkthrough)
5. [API reference](#5-api-reference)
6. [Peeking inside each backend](#6-peeking-inside-each-backend)
7. [Running without Docker](#7-running-without-docker)
8. [Configuration](#8-configuration)
9. [Project layout](#9-project-layout)
10. [Troubleshooting](#10-troubleshooting)
11. [Shutting down and resetting](#11-shutting-down-and-resetting)

---

## 1. What you'll see

When the stack is running, you have:

- A web API at `http://localhost:8000` that lets you log in, manage users, products, and orders, and run a checkout flow.
- A MySQL database holding the 10 seeded users and 10 seeded products.
- A MongoDB collection holding the 3 seeded orders (and any new ones you create).
- A Kafka broker publishing a message every time something changes — creating a user, updating a product, checking out an order, and so on.
- Interactive API docs at `http://localhost:8000/docs` that you can try without writing any code.

Everything above runs inside Docker containers. Nothing gets installed on your laptop except Docker itself.

## 2. How the pieces fit together

```
                    ┌────────────────────────────┐
     curl / browser ─►  FastAPI (port 8000)      │
                    │                            │
                    │  ┌─ users, products ──────►│ MySQL  (port 3306)
                    │  ├─ orders ───────────────►│ Mongo  (port 27017)
                    │  └─ change events ────────►│ Kafka  (port 9092)
                    └────────────────────────────┘
```

Why three stores?

- **MySQL** is a classic relational database — great for things that have a fixed shape and stable identity, like users and products.
- **MongoDB** is a document store — great for things with a variable, nested shape, like an order that contains a list of items.
- **Kafka** is a message bus — every time data changes, the API publishes an event there. Other services (or you, with a console consumer) can subscribe to these topics without touching the API.

A single FastAPI service coordinates the three. For example, when you create an order:

1. The API checks product stock in **MySQL** and decrements it atomically.
2. It writes the order document to **MongoDB**.
3. It publishes an `order.created` event to **Kafka**.

You'll see all three happening in the walkthrough below.

## 3. Quick start (5 minutes)

### What you need

- **Docker** with `docker compose` (Docker Desktop includes both). Nothing else.

### Bring everything up

From the project folder:

```bash
docker compose up -d --build
```

The first run pulls images and builds the API — expect 1–3 minutes. Subsequent runs take seconds.

When it's ready, check that the API is alive:

```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

Open the interactive docs in a browser: **http://localhost:8000/docs**.

That's it — you're running.

## 4. First walkthrough

Each step below is a copy-paste command. Run them in order.

### Step 1: Log in

Every seeded user shares the password `password123`. Log in as Alice:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"password123"}'
```

You'll get back an access token that looks like `{"access_token":"eyJ...","token_type":"bearer"}`. Save it to a shell variable so the rest of the walkthrough can use it:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"password123"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
```

### Step 2: List what's seeded

```bash
# 10 users in MySQL
curl -s http://localhost:8000/users/ -H "Authorization: Bearer $TOKEN"

# 10 products in MySQL (each with a stock count)
curl -s http://localhost:8000/products/ -H "Authorization: Bearer $TOKEN"

# 3 orders in MongoDB
curl -s http://localhost:8000/orders/ -H "Authorization: Bearer $TOKEN"
```

### Step 3: Place an order (watch stock decrement)

The Laptop (product id `1`) starts with a stock of 25. Buy 2:

```bash
# Before
curl -s http://localhost:8000/products/1 -H "Authorization: Bearer $TOKEN"
# {"name":"Laptop","description":"A powerful laptop","price":999.99,"in_stock":true,"id":1,"stock":25}

# Place the order
curl -s -X POST http://localhost:8000/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":1,"quantity":2}]}'

# After — stock is now 23
curl -s http://localhost:8000/products/1 -H "Authorization: Bearer $TOKEN"
```

What just happened:

- The API reserved 2 units of stock in **MySQL** (using a row lock so two orders can't oversubscribe).
- It wrote the new order document to **MongoDB** with the next sequential id.
- It published an `order.created` event to **Kafka** on topic `demo.orders`.

### Step 4: Try to buy more than there is (should fail)

```bash
curl -s -X POST http://localhost:8000/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":1,"quantity":999}]}'
# {"detail":"Insufficient stock for product 1"}  (HTTP 400)
```

### Step 5: Run a checkout with a discount code

`/checkout` is a richer alternative to `/orders` that returns a confirmation number and supports discount codes (`WELCOME10` for 10 % off, `SAVE20` for 20 % off):

```bash
curl -s -X POST http://localhost:8000/checkout/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":3,"quantity":2}],"discount_code":"WELCOME10"}'
```

Sample response:

```json
{
  "confirmation_number": "ORD-A1B2C3D4E5F6",
  "status": "completed",
  "order": { "id": 5, "total": 269.98, "... " : "..." },
  "discount_applied": 30.0
}
```

This publishes a `checkout.completed` event to Kafka.

### Step 6: Get a per-user order summary

```bash
curl -s http://localhost:8000/users/1/orders -H "Authorization: Bearer $TOKEN"
```

This is a cross-store aggregate — it reads orders from MongoDB, resolves product names from MySQL, and returns the user's order count, total spent, and top product.

### Step 7: Create a new user

```bash
curl -s -X POST http://localhost:8000/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Jane Doe","email":"jane@example.com","age":28,"password":"secret"}'
```

Emails must be unique — try the same request twice and the second attempt returns **409 Conflict**.

### Step 8: See the Kafka events you just generated

Open a second terminal and run:

```bash
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic demo.orders --from-beginning --timeout-ms 5000
```

You'll see JSON events like `{"event_type":"order.created","timestamp":"...","payload":{...}}`. There's one per mutation.

## 5. API reference

### Public

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | Liveness probe. No auth. |
| `POST` | `/auth/login` | Exchange email + password for a JWT. |

### Users (MySQL)

| Method | Path | What it does |
|---|---|---|
| `GET` | `/users/` | List all users. |
| `GET` | `/users/{id}` | One user. `404` if not found. |
| `POST` | `/users/` | Create. `409` if email already exists. |
| `PATCH` | `/users/{id}` | Partial update. `409` on email conflict. |
| `DELETE` | `/users/{id}` | Delete user **and all their orders** (cascades to MongoDB). |
| `GET` | `/users/{id}/orders` | Summary: count, total spent, top product, enriched orders. |

### Products (MySQL)

| Method | Path | What it does |
|---|---|---|
| `GET` | `/products/` | List all products including stock. |
| `GET` | `/products/{id}` | One product. |
| `POST` | `/products/` | Create. |
| `PATCH` | `/products/{id}` | Partial update. |
| `DELETE` | `/products/{id}` | Delete. |

### Orders (MongoDB, cross-refs MySQL on read)

| Method | Path | What it does |
|---|---|---|
| `GET` | `/orders/` | List with enriched `user_name` / `product_name` / `price`. |
| `GET` | `/orders/{id}` | One order. |
| `POST` | `/orders/` | Create. Reserves stock atomically; `400` if insufficient. |
| `DELETE` | `/orders/{id}` | Delete. |

### Checkout

| Method | Path | What it does |
|---|---|---|
| `POST` | `/checkout/` | Like `/orders/` but returns a confirmation number and supports a `discount_code`. Emits `checkout.completed`. |

All endpoints except `/health` and `/auth/login` require the header `Authorization: Bearer <token>`.

### Events published to Kafka

| Topic | Events |
|---|---|
| `demo.users` | `user.created`, `user.updated`, `user.deleted` |
| `demo.products` | `product.created`, `product.updated`, `product.deleted` |
| `demo.orders` | `order.created`, `order.updated`, `order.deleted`, `checkout.completed` |

Event shape: `{"event_type": "...", "timestamp": "ISO8601", "payload": {...}}`.

## 6. Peeking inside each backend

Sometimes it's useful to bypass the API and look at the raw data in each store. Everything below uses `docker compose exec`, which runs a command inside an already-running container — no installs needed.

### MySQL

```bash
# Open a MySQL shell
docker compose exec mysql mysql -udemo -pdemo demo_rest

# Inside the shell:
mysql> SHOW TABLES;
mysql> SELECT id, name, email, age FROM users LIMIT 5;
mysql> SELECT id, name, price, stock, in_stock FROM products;
mysql> exit;
```

### MongoDB

```bash
# Open a Mongo shell
docker compose exec mongo mongosh demo_rest

# Inside the shell:
demo_rest> db.orders.find().limit(3).pretty()
demo_rest> db.orders.countDocuments()
demo_rest> db.counters.find()      # the sequential-id bookkeeping
demo_rest> exit
```

### Kafka

```bash
# List topics
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 --list

# Tail events live (leave it running; trigger an API call in another terminal)
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 --topic demo.orders
```

## 7. Running without Docker

Use this if you already have MySQL, MongoDB, and Kafka running locally and want to run the API itself against them.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12+.
2. Install dependencies:

   ```bash
   uv sync
   ```

3. Point the API at your services (defaults shown):

   ```bash
   export DATABASE_URL="mysql+asyncmy://demo:demo@localhost:3306/demo_rest"
   export MONGO_URI="mongodb://localhost:27017"
   export MONGO_DB="demo_rest"
   export KAFKA_BOOTSTRAP="localhost:9092"
   export JWT_SECRET="demo-secret-key-change-in-production"
   ```

4. Start with hot reload:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

Kafka is best-effort — if the broker isn't reachable at startup, the API still comes up and event publishing is silently skipped.

## 8. Configuration

The API reads these environment variables on startup. Defaults (in parentheses) are safe for local development.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `mysql+asyncmy://demo:demo@localhost:3306/demo_rest` | MySQL connection string |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB` | `demo_rest` | MongoDB database name |
| `KAFKA_BOOTSTRAP` | `localhost:9092` | Kafka broker address |
| `JWT_SECRET` | `demo-secret-key-change-in-production` | Secret used to sign access tokens |

Inside `docker compose`, these are set to point containers at each other (e.g. `mysql:3306` instead of `localhost:3306`).

## 9. Project layout

```
app/
├── main.py                     # FastAPI entry point; lifespan wires up MySQL/Mongo/Kafka
├── config.py                   # Reads environment variables
├── security.py                 # Password hash/verify helpers
├── errors.py                   # Typed domain errors (e.g. EmailAlreadyRegistered)
├── dependencies.py             # JWT + session FastAPI dependencies
├── data/
│   ├── mysql.py                # Async engine, Base, session factory
│   ├── mongo.py                # Motor client, sequence counter helper
│   ├── kafka.py                # aiokafka producer, publish helper
│   └── seed.py                 # Seeds 10 users, 10 products, 3 orders on first boot
├── models/
│   ├── auth.py, user.py, product.py, order.py, checkout.py   # Pydantic schemas
│   └── db/
│       ├── user.py             # SQLAlchemy User
│       └── product.py          # SQLAlchemy Product
├── controllers/                # Business logic
│   ├── auth.py, user.py, product.py, order.py, checkout.py
└── routes/                     # HTTP endpoints
    ├── auth.py, health.py, user.py, product.py, order.py, checkout.py
```

## 10. Troubleshooting

**The API container keeps restarting.**
Run `docker compose logs api` to see why. The most common cause is a schema mismatch left over from an older version — do `docker compose down -v` to wipe the volumes, then `docker compose up -d --build` to start fresh.

**`asyncmy` build errors on first `docker compose up`.**
The Dockerfile installs `gcc` and `build-essential` for this. If the image was cached before that change, force a rebuild with `docker compose build --no-cache api`.

**I changed the schema but my queries still fail.**
This project uses `Base.metadata.create_all()`, which only creates missing tables — it doesn't alter existing ones. After changing columns, reset the database with `docker compose down -v`.

**Kafka events never show up.**
The very first publish for a topic can fail because auto-topic-creation takes a moment. Trigger the API call again and the events will flow. To see what's in a topic, use `kafka-console-consumer` as shown in section 6.

**My JWT "expired" quickly.**
Tokens last 30 minutes. Log in again to get a new one.

## 11. Shutting down and resetting

```bash
# Stop containers, keep volumes (data persists for next startup)
docker compose down

# Stop containers and delete all data (fresh seed on next startup)
docker compose down -v

# Restart just the API after code changes
docker compose restart api
```

## Interactive docs

FastAPI auto-generates two docs UIs:

- **Swagger UI**: http://localhost:8000/docs — click the lock icon to paste a token and try calls in the browser.
- **ReDoc**: http://localhost:8000/redoc — read-only reference.

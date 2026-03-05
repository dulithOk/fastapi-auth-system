# 🔐 FastAPI Authentication System

A production-ready authentication and user management API built with **FastAPI**, **SQLAlchemy 2.0 (async)**, **PostgreSQL**, and **JWT-based RBAC**.

---

## ✨ Features

- JWT access + refresh token authentication
- Role-based access control (`admin`, `moderator`, `user`)
- Full CRUD for users with permission guards
- Async SQLAlchemy 2.0 + asyncpg
- Alembic database migrations
- Auto-seeded admin user on startup
- Docker + Docker Compose for dev and production
- Comprehensive error handling with proper HTTP status codes
- OpenAPI docs at `/docs`

---

## 📁 Project Structure

```
fastapi-auth/
├── app/
│   ├── controllers/        # Route handlers (FastAPI routers)
│   │   ├── auth_controller.py
│   │   └── user_controller.py
│   ├── services/           # Business logic layer
│   │   ├── auth_service.py
│   │   └── user_service.py
│   ├── repositories/       # Database access layer (SQLAlchemy queries)
│   │   └── user_repository.py
│   ├── models/             # SQLAlchemy ORM models
│   │   └── user.py
│   ├── schemas/            # Pydantic request/response schemas
│   │   └── user.py
│   ├── core/               # Config, security, database, exceptions
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── middleware/         # FastAPI dependencies (auth, RBAC)
│   │   └── dependencies.py
│   └── main.py             # Application factory & entry point
├── migrations/             # Alembic migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
├── tests/
│   └── test_api.py
├── .env.example
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start (Local)

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- pip

### 1. Clone & configure

```bash
git clone <your-repo>
cd fastapi-auth

cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, etc.
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database

```sql
CREATE DATABASE authdb;
```

### 4. Run Alembic migrations

```bash
alembic upgrade head
```

### 5. Start the development server

```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🐳 Docker Compose (Recommended)

### Development (with hot-reload)

```bash
cp .env.example .env   # configure your .env
docker compose up --build
```

### Production

Remove the volume mount and `--reload` flag from `docker-compose.yml`, then:

```bash
docker compose -f docker-compose.yml up -d --build
```

---

## 🗄️ Database Migrations (Alembic)

| Command | Description |
|---|---|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back last migration |
| `alembic revision --autogenerate -m "your message"` | Generate a new migration |
| `alembic history` | List all migrations |
| `alembic current` | Show current revision |

---

## 🔑 API Endpoints

### Authentication

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Login (JSON) | Public |
| `POST` | `/api/v1/auth/login/form` | Login (OAuth2 form, Swagger) | Public |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | Public |
| `POST` | `/api/v1/auth/logout` | Logout | Public |

### Users

| Method | Path | Description | Required Role |
|---|---|---|---|
| `POST` | `/api/v1/users/register` | Register new user | Public |
| `GET` | `/api/v1/users/me` | Get own profile | Any authenticated |
| `PATCH` | `/api/v1/users/me` | Update own profile | Any authenticated |
| `DELETE` | `/api/v1/users/me` | Delete own account | Any authenticated |
| `GET` | `/api/v1/users/` | List all users (paginated) | moderator, admin |
| `POST` | `/api/v1/users/` | Create user with role | admin |
| `GET` | `/api/v1/users/{id}` | Get user by ID | moderator, admin |
| `PATCH` | `/api/v1/users/{id}` | Update any user | admin |
| `DELETE` | `/api/v1/users/{id}` | Delete any user | admin |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Server health check |

---

## 🔐 Authentication Flow

### 1. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin@123456"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 2. Use the token

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

### 3. Refresh the token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

## 👤 Default Admin Credentials

Set in `.env` (change before deploying!):

```
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=Admin@123456
FIRST_ADMIN_USERNAME=admin
```

The admin account is automatically created on application startup if it doesn't exist.

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | required |
| `DATABASE_URL_SYNC` | Sync PostgreSQL connection string (Alembic CLI) | required |
| `SECRET_KEY` | JWT signing key (min 32 chars) | required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `ALLOWED_ORIGINS` | CORS allowed origins (JSON array) | `["http://localhost:3000"]` |
| `FIRST_ADMIN_EMAIL` | Seeded admin email | `admin@example.com` |
| `FIRST_ADMIN_PASSWORD` | Seeded admin password | `Admin@123456` |
| `DEBUG` | Enable SQLAlchemy query logging | `False` |

---

## 🧪 Running Tests

```bash
pytest tests/ -v --asyncio-mode=auto
```

> **Note:** Tests require a live PostgreSQL database configured in `.env`. For CI, use a separate test database.

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** (via passlib)
- JWTs use **HS256** — switch to **RS256** for multi-service environments
- Access tokens are short-lived (30 min); refresh tokens are 7 days
- For true logout/token blacklisting, integrate **Redis** as a token blocklist
- Always set a strong, random `SECRET_KEY` in production:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- The Dockerfile runs the app as a **non-root user**
- CORS is configured — restrict `ALLOWED_ORIGINS` for production

---

## 📦 Tech Stack

| Library | Version | Purpose |
|---|---|---|
| FastAPI | 0.115.6 | Web framework |
| SQLAlchemy | 2.0.36 | Async ORM |
| Alembic | 1.14.0 | DB migrations |
| asyncpg | 0.30.0 | Async PostgreSQL driver |
| Pydantic | 2.10.3 | Data validation |
| python-jose | 3.3.0 | JWT handling |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| uvicorn | 0.32.1 | ASGI server |

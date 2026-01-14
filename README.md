# TaskFlow API

REST API for task management built with Flask. This project demonstrates API design, authentication, and security. 

There is a CLAUDE.md file with markdown that can help to learn about REST API. 

## Features

- **RESTful Design** - Clean resource-based URLs with proper HTTP methods
- **JWT Authentication** - Secure token-based auth with bcrypt password hashing
- **User Isolation** - Users can only access their own tasks
- **Pagination & Filtering** - Query tasks with sorting, filtering, and pagination
- **Rate Limiting** - Protection against abuse (100 req/min default)
- **Response Caching** - Improved performance with in-memory caching
- **Comprehensive Tests** - 20+ unit tests covering all functionality

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT REQUEST                                  │
│                        (curl, Postman, Frontend)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FLASK APP (app.py)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Rate Limiter│  │   Cache     │  │   Routes    │  │  Middleware │        │
│  │ (100/min)   │  │ (60s TTL)   │  │  Blueprints │  │ (JWT Auth)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
     ┌──────────────────────────┐        ┌──────────────────────────┐
     │     AUTH ROUTES          │        │     TASK ROUTES          │
     │  /auth/register (POST)   │        │  /tasks      (GET/POST)  │
     │  /auth/login    (POST)   │        │  /tasks/:id  (GET/PUT/   │
     │                          │        │               DELETE)    │
     │  Returns: JWT Token      │        │  Requires: Bearer Token  │
     └──────────────────────────┘        └──────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                         MODELS (SQLAlchemy)                     │
     │  ┌─────────────────────┐      ┌─────────────────────────────┐  │
     │  │       USER          │      │           TASK              │  │
     │  │  - id               │      │  - id                       │  │
     │  │  - email            │◄────►│  - title                    │  │
     │  │  - password_hash    │ 1:N  │  - description              │  │
     │  │                     │      │  - completed                │  │
     │  │                     │      │  - user_id (FK)             │  │
     │  └─────────────────────┘      └─────────────────────────────┘  │
     └─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                      SQLite DATABASE                            │
     │                    (instance/taskflow.db)                       │
     └─────────────────────────────────────────────────────────────────┘
```

## Request Flow

```
┌──────────┐     ┌───────────┐     ┌────────────┐     ┌──────────┐     ┌────────┐
│  Client  │────►│   Rate    │────►│    JWT     │────►│  Route   │────►│   DB   │
│          │     │  Limiter  │     │ Middleware │     │ Handler  │     │        │
└──────────┘     └───────────┘     └────────────┘     └──────────┘     └────────┘
     │                │                  │                 │               │
     │           Check limit        Validate token    Process request  Query/Save
     │                │                  │                 │               │
     │           429 if over        401 if invalid    Return JSON     Return data
     │                │                  │                 │               │
     ◄────────────────┴──────────────────┴─────────────────┴───────────────┘
                              Response (JSON)
```

## Project Structure

```
restapi/
├── app.py              # Application entry point & configuration
├── config.py           # JWT settings and environment config
├── middleware.py       # Authentication decorator (@token_required)
├── models.py           # SQLAlchemy models (User, Task)
├── requirements.txt    # Python dependencies
├── routes/
│   ├── __init__.py
│   ├── auth.py         # Authentication endpoints
│   └── tasks.py        # Task CRUD endpoints
├── tests/
│   ├── __init__.py
│   └── test_api.py     # Unit tests
└── instance/
    └── taskflow.db     # SQLite database (auto-generated)
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Create new user account | No |
| POST | `/auth/login` | Get JWT token | No |

### Tasks

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/tasks` | List all tasks (paginated) | Yes |
| GET | `/tasks/:id` | Get single task | Yes |
| POST | `/tasks` | Create new task | Yes |
| PUT | `/tasks/:id` | Update task | Yes |
| DELETE | `/tasks/:id` | Delete task | Yes |

### Query Parameters (GET /tasks)

| Parameter | Example | Description |
|-----------|---------|-------------|
| `page` | `?page=2` | Page number (default: 1) |
| `limit` | `?limit=20` | Results per page (default: 10, max: 100) |
| `completed` | `?completed=true` | Filter by completion status |
| `sort` | `?sort=title` | Sort by field (id, title, completed) |
| `order` | `?order=desc` | Sort direction (asc, desc) |

## Quick Start

### 1. Clone and Setup

```bash
cd restapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

Server starts at `http://localhost:5000`

### 3. Test the API

```bash
# Register a new user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'

# Login and get token
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'

# Use the token to create a task
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"title": "My first task"}'

# Get all tasks
curl http://localhost:5000/tasks \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Run Tests

```bash
pytest tests/ -v
```

## HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Access denied (not owner) |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |

## Security Features

- **Password Hashing** - bcrypt with random salt
- **JWT Tokens** - 1-hour expiration, HS256 algorithm
- **User Isolation** - Tasks filtered by authenticated user
- **Rate Limiting** - Prevents brute-force and DoS attacks
- **Input Validation** - All inputs validated before processing

## Tech Stack

- **Framework**: Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: PyJWT + bcrypt
- **Caching**: Flask-Caching (SimpleCache)
- **Rate Limiting**: Flask-Limiter
- **Testing**: pytest

## License

MIT

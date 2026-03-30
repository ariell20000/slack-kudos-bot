# Kudos Slack Bot

A FastAPI-based Slack bot for sending kudos with JWT authentication, role-based access control, and SQLite persistence.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Features](#features)
- [Slack Commands](#slack-commands)
- [Database Structure](#database-structure)
- [Setup & Run](#setup--run)
- [Testing](#testing)
- [Future Improvements](#future-improvements)

---

## Overview

The bot enables:

- Sending Kudos to other users
- Viewing the number of Kudos sent and received
- Viewing the leaderboard of top users
- Admin actions: promoting users, deactivating users

It provides REST endpoints and a Slack interface, including authentication and role-based access control.

---

## Architecture

```
Slack Command → Router → Service Layer → Database
```

**Layered Design:**

- **Routers** (`routers/`) - Thin HTTP endpoint handlers
- **Services** (`services/`) - Business logic split into focused modules:
  - `auth_service.py` - User registration, login, Slack authentication
  - `user_service.py` - User management (delete, promote, get)
  - `kudos_service.py` - Kudos operations (send, get, delete, leaderboard)
  - `slack_service.py` - Slack command parsing and Block Kit formatting
- **Core** (`core/`) - Configuration, dependencies, logging, security
- **Database** - SQLAlchemy ORM models

---

## Project Structure

```
slack_kudos_bot/
├── main.py              # FastAPI app entry point
├── database.py          # Database connection setup
├── models.py            # Pydantic schemas (validation)
├── models_db.py         # SQLAlchemy ORM models
├── core/
│   ├── config.py        # Environment settings
│   ├── dependencies.py  # FastAPI dependencies (auth, DB)
│   ├── logger.py        # Logging configuration
│   └── security.py      # Password hashing & JWT tokens
├── routers/
│   ├── auth.py          # /register, /login endpoints
│   ├── kudos.py         # /kudos endpoints
│   ├── users.py         # /users endpoints (admin)
│   └── slack.py         # /slack/command endpoint
├── services/
│   ├── auth_service.py
│   ├── kudos_service.py
│   ├── user_service.py
│   └── slack_service.py
└── tests/
    ├── conftest.py      # Test fixtures
    ├── test_auth.py
    ├── test_kudos.py
    ├── test_admin.py
    ├── test_slack_service.py
    └── test_validation.py
```

---

## Features

### Kudos System
- Send Kudos to other users
- Daily limit: 5 Kudos per user
- Cannot send Kudos to oneself
- Only active users can send and receive

### Admin Features
- View all users
- Deactivate / delete users
- Promote users to admin

### Leaderboard
- Displays top users by Kudos received
- Special emojis for top ranks (🔥, 🥇, 🥈, 🥉)

### Security
- Slack request signature verification (HMAC)
- Password hashing with bcrypt
- JWT authentication for REST API
- Role-based access control (user/admin)

---

## Slack Commands

| Command         | Usage                         | Permission     |
|-----------------|-------------------------------|----------------|
| `/kudos`        | `/kudos <username> <message>` | All users      |
| `/mystatus`     | `/mystatus`                   | All users      |
| `/mykudos`      | `/mykudos`                    | All users      |
| `/leaderboard`  | `/leaderboard`                | All users      |
| `/users`        | `/users`                      | Admin only     |
| `/delete`       | `/delete <username>`          | Admin only     |
| `/promote`      | `/promote <username>`         | Admin only     |
| `/help`         | `/help`                       | All users      |

---

## Database Structure

### User
| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `username` | String | Unique username |
| `slack_id` | String | Slack user ID (nullable) |
| `password_hash` | String | Bcrypt hash (nullable for Slack users) |
| `role` | String | `user` or `admin` |
| `is_active` | Boolean | Account status |
| `auth_provider` | String | `local` or `slack` |

### Kudos
| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `from_user_id` | Integer | FK → User |
| `to_user_id` | Integer | FK → User |
| `message` | String | Kudos message |
| `time_created` | DateTime | Timestamp |

---

## Setup & Run

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourusername/slack_kudos_bot.git
cd slack_kudos_bot
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

Required variables:
- `SLACK_SIGNING_SECRET` - From Slack App settings
- `SECRET_KEY` - Random string for JWT signing

### 3. Run the server

```bash
uvicorn main:app --reload
```

Server runs at http://localhost:8000

API docs available at http://localhost:8000/docs

### Docker

```bash
docker build -t slack-kudos-bot .
docker run -p 8000:8000 --env-file .env slack-kudos-bot
```

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_kudos.py
```

---

## Future Improvements

- [ ] Support quoted messages in Slack
- [ ] Async database operations
- [ ] Visual dashboard for Kudos analytics
- [ ] Rate limiting
- [ ] Database migrations with Alembic
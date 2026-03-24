# Kudos Slack Bot

Kudos Slack Bot is an internal Slack bot that allows sending Kudos, viewing leaderboards, and managing users with admin permissions. It is built with **FastAPI**, **SQLAlchemy**, and integrates with Slack using Slash Commands.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Slack Commands](#slack-commands)
- [Database Structure](#database-structure)
- [Setup & Run](#setup--run)
- [Future Improvements](#future-improvements)
- [Flow Diagram](#flow-diagram)

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
Slack Command → Slack Service → Services Layer → Database

- **Slack Service Layer (`slack_service.py`)**  
  Handles Slack request verification, command parsing, Block Kit responses, and logging.

- **Services Layer (`services.py`)**  
  Contains business logic: Kudos handling, user management, leaderboard, and rules (e.g., daily limits).

- **Database**  
  SQLAlchemy models for users and Kudos.

- **Logging**  
  Structured logs for audit and debugging.

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
- Slack request verification
- Local users with encrypted passwords
- Role-based access control
- Only active users can perform actions

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
- `id` (PK)  
- `username` (unique)  
- `slack_id` (nullable)  
- `role` (`user` / `admin`)  
- `is_active` (bool)  
- `password_hash` (nullable for Slack users)

### Kudos
- `id` (PK)  
- `from_user_id` (FK → User)  
- `to_user_id` (FK → User)  
- `message` (text)  
- `time_created` (datetime)  

---

## Setup & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload

Environment Variables (.env):

SLACK_SIGNING_SECRET
DATABASE_URL
Future Improvements
Support quoted messages in Slack
Async handling for better performance
Full unit and integration test coverage
Visual dashboard for Kudos
Rate limiting and analytics
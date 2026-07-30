🎓 COMPLETE BEGINNER'S GUIDE TO YOUR SLACK KUDOS BOT

Everything Explained Like You're in First Year CS

--------------------------------------------------------------------------------------------------------------------------------

📚 TABLE OF CONTENTS

 1. What Is This Project?
 2. Every Library Explained (With Alternatives)
 3. Every File & Directory Explained
 4. Deep Dive: FastAPI
 5. Deep D``ive: Authentication (JWT, bcrypt, OAuth2)
 6. Deep Dive: SQLite vs PostgreSQL
 7. Deep Dive: What is Alembic?
 8. Architecture Patterns Explained
 9. Data Flow Examples
 10. Interview Answers

--------------------------------------------------------------------------------------------------------------------------------

1️⃣ WHAT IS THIS PROJECT?

You built a Slack Bot that lets people send "kudos" (praise) to each other. It has:

 - Slack integration: Users type /kudos @alice Great job! in Slack
 - REST API: Web endpoints for registration, login, viewing kudos
 - Authentication: Two ways to log in (username/password OR via Slack)
 - Database: Stores users and kudos messages
 - Security: Passwords are hashed, tokens expire, Slack requests are verified

Real-world analogy: Think of it as a digital "thank you card" system. Instead of buying a card, you send kudos through Slack. The
bot tracks who sent what, and stores it in a database.

--------------------------------------------------------------------------------------------------------------------------------

2️⃣ EVERY LIBRARY EXPLAINED

Let me explain every single line in requirements.txt:

📦 requirements.txt (12 libraries)

 # Web framework
 fastapi>=0.100.0
 uvicorn>=0.20.0
 typing_extensions>=4.6.0

 # Database
 sqlalchemy>=2.0.0

 # Authentication & Security
 passlib[bcrypt]>=1.7.4
 bcrypt==4.0.1
 python-jose[cryptography]>=3.3.0

 # Configuration
 python-dotenv>=1.0.0
 pydantic-settings>=2.0.0

 # Form parsing (Slack commands)
 python-multipart>=0.0.6

 # Testing
 pytest>=7.0.0

--------------------------------------------------------------------------------------------------------------------------------

1. FastAPI (>=0.100.0) - The Web Framework

What it is: A modern Python framework for building APIs (Application Programming Interfaces).

What's an API? Think of an API as a waiter in a restaurant:

 - You (the client) tell the waiter "I want pasta"
 - The waiter takes your order to the kitchen (the server)
 - The kitchen prepares the food
 - The waiter brings it back to you

In your project, FastAPI handles HTTP requests like:

 - POST /register → "Create a new user"
 - GET /kudos/mykudos → "Show me my kudos"
 - POST /slack/command → "Process a Slack command"

Why FastAPI?

 - ✅ Automatic documentation: Visit http://localhost:8000/docs and you get a beautiful interactive API explorer
 - ✅ Fast: Built on modern async Python (can handle many requests at once)
 - ✅ Type checking: Uses Python type hints to catch errors before they happen
 - ✅ Dependency injection: Automatically provides things like database connections (more on this later)

Alternatives:

 - Flask: Older, simpler, but no automatic docs, no async by default
 - Django: Full-featured (includes admin panel, ORM, authentication), but overkill for a simple API
 - Express.js: Node.js framework (different language)

Interview Answer: "I chose FastAPI because it automatically generates API documentation, has built-in dependency injection, and
supports async operations. For a microservice like a Slack bot, I didn't need Django's full web framework features like templates
and admin panel."

--------------------------------------------------------------------------------------------------------------------------------

2. Uvicorn (>=0.20.0) - The ASGI Server

What it is: The "engine" that runs your FastAPI application.

Analogy: FastAPI is like the car (the application), and Uvicorn is the engine that makes it run.

What does it do?

 - Listens for HTTP requests on port 8000
 - Passes requests to FastAPI
 - Sends responses back to clients

The command to start it:

 uvicorn main:app --reload

 - main = the filename (main.py)
 - app = the FastAPI instance inside main.py
 - --reload = auto-restart when you change code

Alternatives:

 - Gunicorn: Older, sync-only (can't handle async functions)
 - Hypercorn: Similar to Uvicorn, less popular

Interview Answer: "Uvicorn is an ASGI server optimized for async Python frameworks. Since FastAPI uses async/await, Uvicorn is
the recommended server for production."

--------------------------------------------------------------------------------------------------------------------------------

3. SQLAlchemy (>=2.0.0) - The ORM (Object-Relational Mapper)

What it is: A library that lets you talk to databases using Python objects instead of writing raw SQL.

Without SQLAlchemy (raw SQL):

 cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
 user = cursor.fetchone()

With SQLAlchemy (Python objects):

 user = db.query(User).filter(User.username == username).first()

Why this is amazing:

 1. Type safety: Your IDE can autocomplete User.username
 2. Database independence: Works with SQLite, PostgreSQL, MySQL, etc. (just change the connection URL)
 3. Relationships: Automatically load related data (e.g., user.received_kudos)

Alternatives:

 - Django ORM: Only works with Django
 - Peewee: Simpler but less powerful
 - Raw SQL: Full control, but error-prone and repetitive

Interview Answer: "SQLAlchemy provides database abstraction, so I can develop with SQLite and deploy with PostgreSQL by just
changing the connection string. It also gives me type-safe queries and automatic relationship loading."

--------------------------------------------------------------------------------------------------------------------------------

4. Passlib[bcrypt] (>=1.7.4) + bcrypt (4.0.1) - Password Hashing

What it is: Libraries for securely storing passwords.

🚨 The Golden Rule: NEVER store passwords in plain text!

Why? If someone hacks your database, they'll see everyone's passwords.

How bcrypt works:

 1. User enters password: "mypassword123"
 2. bcrypt adds random "salt" and hashes it: $2b$12$Kix... (60 characters)
 3. You store the hash in the database
 4. When user logs in, you hash their input and compare hashes

Example:

 # When user registers
 hashed = pwd_context.hash("mypassword123")
 # Result: "$2b$12$Kix7vF8..."

 # When user logs in
 is_correct = pwd_context.verify("mypassword123", hashed)
 # Result: True

Why bcrypt specifically?

 - Slow by design: Takes ~100ms to hash a password (makes brute-force attacks impractical)
 - Salted: Each password gets a random salt (prevents rainbow table attacks)
 - Industry standard: Used by major companies

Alternatives:

 - Argon2: Newer, more secure, but less widely supported
 - SHA-256: Fast but insecure for passwords (too easy to crack)

Interview Answer: "I use bcrypt through passlib because it's the industry standard for password hashing. It's slow by design to
prevent brute-force attacks, and it automatically salts each password."

--------------------------------------------------------------------------------------------------------------------------------

5. python-jose[cryptography] (>=3.3.0) - JWT Token Handling

What it is: A library for creating and validating JWT (JSON Web Tokens).

What's a JWT? A token that proves "I am user Alice" without needing to store sessions on the server.

Structure of a JWT:

 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTcxNjg0MjQwMH0.SflKxwRJ...
 │                                      │                                        │
 │        HEADER (Base64)               │        PAYLOAD (Base64)                │    SIGNATURE
 │  {"alg":"HS256","typ":"JWT"}         │  {"sub":"alice","exp":1716842400}      │  (HMAC-SHA256)

How it works:

 1. User logs in with username/password
 2. Server creates a JWT with {"sub": "alice", "exp": <timestamp>}
 3. Server signs it with SECRET_KEY (so no one can forge it)
 4. Server sends JWT to user
 5. User includes JWT in all future requests: Authorization: Bearer eyJhbG...
 6. Server verifies the signature and checks expiration

Why JWT?

 - ✅ Stateless: No need to store sessions in a database
 - ✅ Scalable: Works across multiple servers (no shared session storage)
 - ✅ Mobile-friendly: Just send the token in the Authorization header

Trade-offs:

 - ❌ Can't revoke instantly: If you issue a 60-minute token, it's valid for 60 minutes (even if you "delete" the user)
 - ❌ Larger than session IDs: Cookies are ~20 bytes, JWTs are ~200+ bytes

Alternatives:

 - Session cookies: Store session_id on server, send cookie to client (requires database for sessions)
 - OAuth2 tokens: More complex, requires OAuth provider (Google, GitHub)

Interview Answer: "JWT tokens are stateless, meaning I don't need a sessions table in my database. This makes the API scalable
because any server instance can validate the token without shared state. The trade-off is I can't instantly revoke tokens, but
with a 60-minute expiration, the risk window is small."

--------------------------------------------------------------------------------------------------------------------------------

6. python-dotenv (>=1.0.0) + pydantic-settings (>=2.0.0) - Configuration Management

What they do:

 - python-dotenv: Loads variables from .env file
 - pydantic-settings: Validates and type-checks those variables

Why separate .env from code? 🚨 Security: You don't want to commit secrets to GitHub!

Example .env:

 SECRET_KEY=abc123def456...
 SLACK_SIGNING_SECRET=789xyz...

How it's loaded (core/config.py):

 from pydantic_settings import BaseSettings

 class Settings(BaseSettings):
     SECRET_KEY: str  # Required
     SLACK_SIGNING_SECRET: str  # Required
     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Optional with default

     model_config = ConfigDict(env_file=".env")

 settings = Settings()  # Loads .env and validates types

What if you forget to set SECRET_KEY? → Error at startup: Field required [type=missing, input_value=...]

Alternatives:

 - os.environ[]: No validation, crashes at runtime if missing
 - Config files (YAML, JSON): More verbose, harder to keep secrets out of Git

Interview Answer: "I use pydantic-settings to load environment variables with type validation. This catches configuration errors
at startup instead of runtime. python-dotenv lets me keep secrets in a .env file that's gitignored."

--------------------------------------------------------------------------------------------------------------------------------

7. python-multipart (>=0.0.6) - Form Parsing

What it is: Parses HTML form data (used by Slack commands).

Why needed? When Slack sends a slash command (/kudos @alice Great!), it uses the format application/x-www-form-urlencoded:

 token=abc123&user_id=U12345&text=@alice+Great!

This library parses it into a Python dictionary.

Alternatives:

 - Built into FastAPI (if you install python-multipart)

Interview Answer: "Slack commands send form-encoded data, so python-multipart is required by FastAPI to parse that format."

--------------------------------------------------------------------------------------------------------------------------------

8. pytest (>=7.0.0) - Testing Framework

What it is: The most popular Python testing framework.

Example test:

 def test_register_user(db_session):
     user_data = UserCreate(username="alice", password="pass1234")
     result = register_user(user_data, db_session)
     assert result["status"] == "created"

Why pytest?

 - ✅ Simple assert statements (no self.assertEqual(...) like unittest)
 - ✅ Fixtures: Reusable setup code (e.g., db_session creates a fresh database for each test)
 - ✅ Plugins: Coverage reports, async support, etc.

Alternatives:

 - unittest: Built into Python, but more verbose
 - nose: Older, less maintained

Interview Answer: "pytest is the industry standard for Python testing. I use fixtures to create isolated in-memory databases for
each test, ensuring tests don't interfere with each other."

9. typing_extensions (>=4.6.0) - TypedDict for Pydantic Response Models

What it is: A backport package that provides newer `typing` features (like `TypedDict`) on older Python versions.

Why it's here: Several services (e.g. kudos_service.py) use TypedDict classes as FastAPI response-model type hints. Pydantic v2
requires TypedDict to come from `typing_extensions`, not `typing`, on Python < 3.12 - otherwise it raises a PydanticUserError
during route registration. This project's Docker image runs Python 3.11, so this actually broke the deployed app once (it worked
locally on newer Python, and passed CI too, since the tests never built the full FastAPI app to exercise route registration -
tests/test_app.py was added specifically to catch this class of bug going forward).

Interview Answer: "I hit a real bug where response models using `typing.TypedDict` crashed the app on startup, but only on Python
< 3.12 - which was invisible locally and in CI because our tests never built the actual FastAPI app object, just the service
functions. The fix was switching to `typing_extensions.TypedDict`, and I added a test that builds the real app via TestClient so
this class of environment-specific bug fails in CI instead of only in production."

--------------------------------------------------------------------------------------------------------------------------------

3️⃣ EVERY FILE & DIRECTORY EXPLAINED

📁 Project Structure

 slack_kudos_bot/
 ├── main.py               ← App entry point
 ├── database.py           ← SQLite connection setup
 ├── models.py             ← Pydantic schemas (input/output validation)
 ├── models_db.py          ← SQLAlchemy ORM models (database tables)
 ├── requirements.txt      ← Dependencies list
 ├── Dockerfile            ← Docker build instructions (respects Render's $PORT)
 ├── render.yaml           ← Render deployment blueprint (service + env vars)
 ├── .env / .env.example   ← Environment variables
 ├── kudos.db              ← SQLite database file (created at runtime)
 ├── app.log               ← Application logs
 ├── docs/
 │   └── demo.gif          ← README demo recording
 │
 ├── core/                 ← Cross-cutting concerns
 │   ├── config.py         ← Settings class (loads .env)
 │   ├── dependencies.py   ← FastAPI dependencies (get_db, get_current_user)
 │   ├── security.py       ← JWT + password hashing
 │   └── logger.py         ← Logging setup
 │
 ├── routers/              ← HTTP endpoint handlers (thin layer)
 │   ├── auth.py           ← /register, /login
 │   ├── kudos.py          ← POST /kudos, GET /leaderboard, GET /kudos/mykudos, GET /kudos/mystatus
 │   ├── users.py          ← GET /users/data (admin), DELETE /user/{username} (admin)
 │   └── slack.py          ← /slack/command (handles Slack requests)
 │
 ├── services/             ← Business logic (thick layer)
 │   ├── auth_service.py   ← User registration, login, Slack auth
 │   ├── kudos_service.py  ← Add kudos, get kudos, daily limits, paginated leaderboard
 │   ├── user_service.py   ← Admin operations (promote, delete, paginated user list)
 │   └── slack_service.py  ← Slack signature verification, command parsing
 │
 └── tests/                ← Unit & integration tests
     ├── conftest.py       ← Test fixtures (in-memory database)
     ├── test_app.py       ← Builds the real FastAPI app via TestClient
     ├── test_auth.py      ← Test registration, login
     ├── test_kudos.py     ← Test kudos creation, leaderboard
     ├── test_admin.py     ← Test admin operations
     ├── test_slack_service.py ← Test Slack integration
     └── test_validation.py    ← Test Pydantic validators

--------------------------------------------------------------------------------------------------------------------------------

📄 FILE-BY-FILE BREAKDOWN

1. main.py (13 lines) - The Entry Point

 from fastapi import FastAPI
 from database import engine
 from models_db import Base
 from routers import auth, kudos, users, slack

 Base.metadata.create_all(bind=engine)  # Creates tables on startup

 app = FastAPI(title="Kudos Slack Bot API", ...)  # Creates FastAPI instance

 app.include_router(slack.router, prefix="/slack", tags=["Slack"])
 app.include_router(auth.router)  # Adds /register, /login
 app.include_router(kudos.router)  # Adds /kudos/*
 app.include_router(users.router)  # Adds /users/*

 @app.get("/health")
 def health_check():
     return {"status": "healthy"}

What it does:

 1. Creates database tables (Base.metadata.create_all)
 2. Creates FastAPI app instance
 3. Registers routers (groups of endpoints)
 4. Starts the API (when you run uvicorn main:app)

--------------------------------------------------------------------------------------------------------------------------------

2. database.py (16 lines) - Database Setup

 from sqlalchemy import create_engine
 from sqlalchemy.orm import sessionmaker, declarative_base

 DATABASE_URL = "sqlite:///./kudos.db"  # File-based SQLite database

 engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
 SessionLocal = sessionmaker(bind=engine)
 Base = declarative_base()

Key concepts:

 1. ENGINE: The connection to the database
 - create_engine("sqlite:///./kudos.db") → Creates kudos.db file in project root
 - check_same_thread=False → Allows multiple threads to use the same SQLite connection (needed for FastAPI)
 2. SessionLocal: A factory that creates database sessions
 - Each request gets its own session
 - Sessions are like "conversations" with the database
 3. Base: The parent class for all ORM models
 - class User(Base): → User table in the database

--------------------------------------------------------------------------------------------------------------------------------

3. models.py (143 lines) - Pydantic Schemas

Purpose: Define how data enters and exits your API.

Example:

 class UserCreate(BaseModel):
     username: Annotated[str, AfterValidator(is_empty), AfterValidator(too_short(2))]
     password: Annotated[str, AfterValidator(contains_no_spaces)]

What this does:

 1. When someone sends POST /register, FastAPI:
 - Parses the JSON body
 - Validates each field (is_empty, too_short, etc.)
 - If valid, creates a UserCreate object
 - If invalid, returns 422 Unprocessable Entity with error details

Custom validators:

 - is_empty(s) → Rejects "" or "   "
 - too_short(n) → Rejects strings shorter than n
 - contains_no_spaces(s) → Rejects "my password"
 - is_alphanumeric_or_underscore(s) → Only allows [a-zA-Z0-9_]

Interview Answer: "Pydantic schemas validate input data before it reaches my business logic. This prevents invalid data from
entering the database and provides clear error messages to API users."

--------------------------------------------------------------------------------------------------------------------------------

4. models_db.py (40 lines) - SQLAlchemy ORM Models

Purpose: Define database tables and relationships.

 class User(Base):
     __tablename__ = "users"

     id = Column(Integer, primary_key=True)
     username = Column(String, unique=True, index=True)
     password_hash = Column(String, nullable=True)
     slack_id = Column(String, unique=True, nullable=True)
     role = Column(String, default="user")  # user / admin
     is_active = Column(Boolean, default=True)

     received_kudos = relationship("KudosDB", foreign_keys=[KudosDB.to_user_id])
     given_kudos = relationship("KudosDB", foreign_keys=[KudosDB.from_user_id])

What this creates in SQLite:

 CREATE TABLE users (
     id INTEGER PRIMARY KEY,
     username VARCHAR UNIQUE,
     password_hash VARCHAR,
     slack_id VARCHAR UNIQUE,
     role VARCHAR DEFAULT 'user',
     is_active BOOLEAN DEFAULT 1
 );

Relationships:

 - received_kudos → List of kudos sent TO this user
 - given_kudos → List of kudos sent BY this user

You can now do:

 user = db.query(User).filter(User.username == "alice").first()
 for kudos in user.received_kudos:
     print(kudos.message)

--------------------------------------------------------------------------------------------------------------------------------

5. core/config.py (22 lines) - Configuration

 class Settings(BaseSettings):
     SLACK_SIGNING_SECRET: str  # From Slack app settings
     SECRET_KEY: str  # For JWT signing
     ALGORITHM: str = "HS256"  # JWT algorithm
     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
     DAILY_KUDOS_LIMIT: int = 5

     model_config = ConfigDict(env_file=".env")

 settings = Settings()  # Loads .env automatically

What this does:

 - Reads .env file
 - Validates all required fields
 - Provides type-safe access: settings.SECRET_KEY

--------------------------------------------------------------------------------------------------------------------------------

6. core/security.py (89 lines) - Authentication Logic

Four key functions:

 1. hash_password(password) → bcrypt hash
 2. verify_password(plain, hashed) → True/False
 3. create_access_token(data) → JWT string
 4. decode_access_token(token) → dict or None

Example:

 # Registration
 hashed = hash_password("mypassword123")
 # Store hashed in database

 # Login
 if verify_password("mypassword123", user.password_hash):
     token = create_access_token({"sub": user.username})
     return {"access_token": token}

--------------------------------------------------------------------------------------------------------------------------------

7. core/dependencies.py (80 lines) - FastAPI Dependency Injection

Three dependencies:

1. get_db() - Provides database session

 def get_db():
     db = SessionLocal()
     try:
         yield db  # Give session to endpoint
         db.commit()  # Save changes if successful
     except:
         db.rollback()  # Undo changes if error
     finally:
         db.close()  # Always close session

Usage:

 @app.post("/register")
 def register(user: UserCreate, db: Session = Depends(get_db)):
     # db is automatically injected here!

2. get_current_user(token, db) - Extracts user from JWT

 def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
     payload = decode_access_token(token)
     username = payload.get("sub")
     user = db.query(User).filter(User.username == username).first()
     return user

Usage:

 @app.get("/kudos/mykudos")
 def my_kudos(current_user: User = Depends(get_current_user)):
     # current_user is the logged-in user!

3. require_admin(current_user) - Enforces admin role

 def require_admin(current_user: User = Depends(get_current_user)):
     if current_user.role != "admin":
         raise HTTPException(403, "Admin privileges required")
     return current_user

--------------------------------------------------------------------------------------------------------------------------------

🗂️ DIRECTORY BREAKDOWN

routers/ - HTTP Endpoint Handlers

Thin layer: Just parse requests, call services, return responses.

Example: routers/auth.py

 @router.post("/register")
 def register(user: UserCreate, db: Session = Depends(get_db)):
     return auth_service.register_user(user, db)  # Delegates to service

Why separate routers from services?

 - ✅ Testability: You can test auth_service.register_user() without making HTTP requests
 - ✅ Reusability: Same service can be used by HTTP endpoints AND Slack commands

--------------------------------------------------------------------------------------------------------------------------------

services/ - Business Logic

Thick layer: All the important logic lives here.

Example: services/kudos_service.py

 def add_kudos(to_user, message, from_user, db):
     # 1. Validate users exist and are active
     # 2. Check daily kudos limit (5 per day)
     # 3. Prevent self-kudos
     # 4. Create KudosDB entry
     # 5. Log the action
     # 6. Return response

Why put logic in services?

 - ✅ Shared logic: Both /kudos/add (REST API) and /slack/command call add_kudos()
 - ✅ Easy to test: Just pass a mock database session

--------------------------------------------------------------------------------------------------------------------------------

tests/ - Automated Tests

conftest.py - Test fixtures:

 @pytest.fixture(scope="function")
 def db_session():
     engine = create_engine("sqlite:///:memory:")  # In-memory database
     Base.metadata.create_all(engine)
     session = SessionLocal()
     yield session
     session.close()
     Base.metadata.drop_all(engine)  # Clean up after test

Why in-memory database?

 - ✅ Fast: No disk I/O
 - ✅ Isolated: Each test gets a fresh database
 - ✅ No cleanup needed: Disappears after test

Example test (test_auth.py):

 def test_register_user(db_session):
     user = UserCreate(username="alice", password="pass1234")
     result = register_user(user, db_session)
     assert result["status"] == "created"

     # Verify user exists in database
     db_user = db_session.query(User).filter(User.username == "alice").first()
     assert db_user is not None

--------------------------------------------------------------------------------------------------------------------------------

4️⃣ DEEP DIVE: FastAPI

What Makes FastAPI Special?

1. Automatic API Documentation

When you run your app and visit http://localhost:8000/docs, you see this:

Image: Swagger UI → https://fastapi.tiangolo.com/img/index/index-01-swagger-ui-simple.png

You can:

 - See all endpoints
 - Try them with "Try it out" button
 - See request/response schemas
 - See validation errors

How does it work? FastAPI uses your type hints:

 @app.post("/register")
 def register(user: UserCreate, db: Session = Depends(get_db)) -> StatusResponse:
     #           ^^^^^^^^^^^^                               ^^^^^^^^^^^^^^^
     #           Request body schema                        Response schema

FastAPI automatically generates OpenAPI (Swagger) spec from this.

2. Dependency Injection

Problem: You need a database session in every endpoint.

Bad solution:

 def register(user: UserCreate):
     db = SessionLocal()  # Create session manually
     # ... do stuff
     db.close()  # Remember to close!

FastAPI solution:

 def register(user: UserCreate, db: Session = Depends(get_db)):
     # db is automatically injected and closed

How it works:

 1. FastAPI sees Depends(get_db)
 2. Calls get_db() before your function
 3. Passes the result as db
 4. After your function, runs finally: block (closes session)

Benefit: No boilerplate code, automatic cleanup.

3. Type Validation

Bad input:

 POST /register
 {"username": "a", "password": ""}

FastAPI response:

 {
   "detail": [
     {"loc": ["body", "username"], "msg": "Field must be at least 2 characters long"},
     {"loc": ["body", "password"], "msg": "Field cannot be empty"}
   ]
 }

You didn't write any validation code! Pydantic did it for you.

4. Async Support

Sync endpoints:

 @app.get("/users")
 def get_users(db: Session = Depends(get_db)):
     return db.query(User).all()  # Blocks until query finishes

Async endpoints (if you used async libraries):

 @app.get("/users")
 async def get_users(db: AsyncSession = Depends(get_db)):
     return await db.execute(select(User))  # Non-blocking

Why async? Can handle 10,000 concurrent requests instead of 100.

--------------------------------------------------------------------------------------------------------------------------------

5️⃣ DEEP DIVE: Authentication (JWT, bcrypt, OAuth2)

The Complete Authentication Flow

Registration Flow:

 User sends:
 POST /register
 {"username": "alice", "password": "mypassword123"}

        ↓

 1. FastAPI validates input (Pydantic)
    - Username: 2-20 chars, alphanumeric
    - Password: 4-30 chars, no spaces

        ↓

 2. auth_service.register_user() is called
    - Check if username exists
    - Hash password with bcrypt
    - Create User in database

        ↓

 3. Password hashing (bcrypt):
    Input: "mypassword123"
    Hashed: "$2b$12$Kix7vF8LhXyDn8yB0gZXV.0Xr7WJZ..."
    ^^^^    ^^  ^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^
    Algorithm|  Salt (random)          Hash
            Cost factor (12 = 2^12 iterations)

        ↓

 4. Store in database:
    User(username="alice", password_hash="$2b$12$Kix...")

        ↓

 Response: {"status": "created"}

Why salt? If two users have the same password, their hashes are different:

 alice: "password123" → "$2b$12$ABC...XYZ"
 bob:   "password123" → "$2b$12$DEF...UVW"  (different!)

--------------------------------------------------------------------------------------------------------------------------------

Login Flow (JWT Creation):

 User sends:
 POST /login
 {"username": "alice", "password": "mypassword123"}

        ↓

 1. Query database for user
    user = db.query(User).filter(User.username == "alice").first()

        ↓

 2. Verify password
    verify_password("mypassword123", user.password_hash)
    → Hashes input and compares with stored hash

        ↓

 3. Create JWT token
    payload = {"sub": "alice", "exp": 1716842400}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        ↓

 4. Sign token (HMAC-SHA256):
    signature = HMAC-SHA256(header + payload, SECRET_KEY)
    token = base64(header) + "." + base64(payload) + "." + signature

        ↓

 Response:
 {
   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTcxNjg0MjQwMH0.SflKxwRJ...",
   "token_type": "bearer"
 }

--------------------------------------------------------------------------------------------------------------------------------

Authenticated Request Flow:

 User sends:
 GET /kudos/mykudos
 Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        ↓

 1. FastAPI sees `current_user: User = Depends(get_current_user)`

        ↓

 2. OAuth2PasswordBearer extracts token from header
    token = request.headers["Authorization"].split("Bearer ")[1]

        ↓

 3. decode_access_token(token)
    - Verify signature with SECRET_KEY
    - Check expiration ("exp" field)
    - Extract username from "sub" field

        ↓

 4. Query database
    user = db.query(User).filter(User.username == "alice").first()

        ↓

 5. Return user object to endpoint
    def my_kudos(current_user: User = Depends(get_current_user)):
        # current_user is now the User object!

--------------------------------------------------------------------------------------------------------------------------------

Why JWT vs Sessions?

Session-based authentication:

 Client → POST /login → Server creates session in database
                         Server sends session_id cookie
 Client → GET /profile (with cookie) → Server looks up session in DB

Pros:

 - ✅ Can revoke instantly (delete session from DB)
 - ✅ Small cookie size (~20 bytes)

Cons:

 - ❌ Requires database query on every request
 - ❌ Doesn't scale across multiple servers (needs shared session storage)

JWT-based authentication:

 Client → POST /login → Server creates JWT (no database entry)
                         Server sends JWT to client
 Client → GET /profile (with JWT) → Server verifies signature (no DB query)

Pros:

 - ✅ Stateless: No database lookup needed
 - ✅ Scalable: Works across multiple servers (no shared state)
 - ✅ Mobile-friendly: Just include in Authorization header

Cons:

 - ❌ Can't revoke instantly: Token valid until expiration
 - ❌ Larger: ~200 bytes vs ~20 bytes

Your solution:

 - JWT with short expiration (60 minutes)
 - If user is compromised, worst case is 60 minutes of access

Interview Answer: "I chose JWT for stateless authentication. The trade-off is I can't revoke tokens instantly, but with a
60-minute expiration window, the risk is acceptable. For a high-security system, I could implement a token blacklist or use
refresh tokens with shorter access token lifetimes."

--------------------------------------------------------------------------------------------------------------------------------

OAuth2PasswordBearer - What Is It?

This line appears in core/dependencies.py:

 oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

What it does:

 1. Tells FastAPI: "This API uses OAuth2 with password flow"
 2. In Swagger docs: Adds "Authorize" button
 3. Extracts token from Authorization: Bearer <token> header
 4. Returns the token string (you then decode it)

It's NOT full OAuth2! It's just the "password grant" flow:

 - User sends username/password
 - Server returns token
 - User includes token in future requests

Full OAuth2 (like "Login with Google"):

 - User clicks "Login with Google"
 - Redirected to Google
 - Google sends authorization code
 - You exchange code for token

Why use OAuth2PasswordBearer?

 - ✅ Standard HTTP header format
 - ✅ Works with Swagger UI
 - ✅ Compatible with OAuth2 clients

--------------------------------------------------------------------------------------------------------------------------------

6️⃣ DEEP DIVE: SQLite vs PostgreSQL

What is SQLite?

Definition: A file-based database engine. Your entire database is a single file (kudos.db).

How it works:

 DATABASE_URL = "sqlite:///./kudos.db"

This creates kudos.db in your project folder.

Architecture:

 Your App ─────┐
               │
 Uvicorn ──────┤ → All read/write to `kudos.db` file
               │
 FastAPI ──────┘

--------------------------------------------------------------------------------------------------------------------------------

SQLite vs PostgreSQL - The Full Comparison

┌───────────────────────┬───────────────────────────────────────────┬─────────────────────────────────────┐
│ Feature               │ SQLite                                    │ PostgreSQL                          │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Setup                 │ ✅ Zero config (just a file)              │ ❌ Install server + create database │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Speed (reads)         │ ⚡ Very fast (file I/O)                   │ ⚡ Fast (network overhead)          │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Speed (writes)        │ 🐌 One write at a time                    │ ⚡ Many concurrent writes           │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Scale                 │ ⚠️ Good for <100K rows                    │ ✅ Good for millions/billions       │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Concurrent writes     │ ❌ LOCKS THE ENTIRE DATABASE              │ ✅ Row-level locks                  │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Data types            │ ⚠️ Limited (no TRUE/FALSE, stores as 0/1) │ ✅ Rich (JSON, arrays, UUIDs)       │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Transactions          │ ✅ Yes (ACID compliant)                   │ ✅ Yes (ACID compliant)             │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Migrations            │ ⚠️ Manual (or Alembic)                    │ ✅ Alembic                          │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Backup                │ ✅ Copy the .db file                      │ ⚠️ pg_dump command                  │
├───────────────────────┼───────────────────────────────────────────┼─────────────────────────────────────┤
│ Production ready      │ ⚠️ For low-traffic apps                   │ ✅ For high-traffic apps            │
└───────────────────────┴───────────────────────────────────────────┴─────────────────────────────────────┘

--------------------------------------------------------------------------------------------------------------------------------

The BIG Difference: Write Concurrency

SQLite's Write Lock:

Imagine 3 users trying to send kudos at the same time:

 User A → POST /kudos/add  ─┐
                             ├→ SQLite LOCKS the entire database
 User B → POST /kudos/add  ─┤   (B and C must WAIT)
                             │
 User C → POST /kudos/add  ─┘

What happens:

 1. User A's request starts writing
 2. SQLite locks kudos.db
 3. User B's request tries to write → BLOCKED (waits for A to finish)
 4. User C's request tries to write → BLOCKED (waits in queue)

In practice:

 - Low traffic (10 requests/second): No problem
 - High traffic (1000 requests/second): Requests time out

--------------------------------------------------------------------------------------------------------------------------------

PostgreSQL's Row-Level Locks:

 User A → POST /kudos/add (row 1) ─┐
                                    ├→ PostgreSQL allows all 3
 User B → POST /kudos/add (row 2) ─┤   (different rows, no conflict)
                                    │
 User C → POST /kudos/add (row 3) ─┘

What happens:

 1. All 3 requests write simultaneously
 2. PostgreSQL locks only the rows being modified
 3. No waiting (unless two requests modify the same row)

--------------------------------------------------------------------------------------------------------------------------------

Other SQLite Limitations

1. No True Boolean Type

SQLite:

 is_active BOOLEAN  -- Actually stored as INTEGER (0 or 1)

PostgreSQL:

 is_active BOOLEAN  -- True native type

Impact: Minor (Python ORMs handle conversion)

2. Limited ALTER TABLE

SQLite: Can't rename columns, can't change types (must recreate table)

PostgreSQL: Full ALTER TABLE support

Impact: Makes migrations harder

3. No Network Access

SQLite: Must be on the same machine as the app

PostgreSQL: Can be on a different server

Impact: Can't use managed database services (AWS RDS, Heroku Postgres)

--------------------------------------------------------------------------------------------------------------------------------

When to Use Each?

┌───────────────────────────────────────┬─────────────────────┬────────────────┐
│ Use Case                              │ SQLite              │ PostgreSQL     │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ Development                           │ ✅ Perfect          │ ⚠️ Extra setup │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ Prototypes/MVPs                       │ ✅ Perfect          │ ⚠️ Overkill    │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ Personal projects                     │ ✅ Great            │ ⚠️ Unnecessary │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ Low-traffic apps (<100 req/min)       │ ✅ Fine             │ ✅ Fine        │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ High-traffic apps (>1000 req/min)     │ ❌ Too slow         │ ✅ Ideal       │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ Multiple app servers                  │ ❌ Can't share file │ ✅ Central DB  │
├───────────────────────────────────────┼─────────────────────┼────────────────┤
│ Analytical queries                    │ ⚠️ OK               │ ✅ Better      │
└───────────────────────────────────────┴─────────────────────┴────────────────┘

--------------------------------------------------------------------------------------------------------------------------------

Migration Path: SQLite → PostgreSQL

The beauty of SQLAlchemy: Change one line and you're on PostgreSQL!

Before (database.py):

 DATABASE_URL = "sqlite:///./kudos.db"

After:

 DATABASE_URL = "postgresql://user:password@localhost:5432/kudos"

That's it! Your models, queries, everything else stays the same.

Interview Answer: "I chose SQLite for rapid development because it requires zero configuration. Since I used SQLAlchemy as my
ORM, migrating to PostgreSQL is just changing the connection URL. For production with high traffic, I'd switch to PostgreSQL for
better write concurrency and use Alembic for database migrations."

--------------------------------------------------------------------------------------------------------------------------------

7️⃣ DEEP DIVE: What is Alembic?

The Problem Alembic Solves

Scenario: You deploy your app with this User table:

 class User(Base):
     id = Column(Integer, primary_key=True)
     username = Column(String)
     password_hash = Column(String)

Two months later, you want to add email field:

 class User(Base):
     id = Column(Integer, primary_key=True)
     username = Column(String)
     password_hash = Column(String)
     email = Column(String)  # NEW FIELD

Problem: Your production database still has the old schema! Users are already in the database!

Bad solution:

 DROP TABLE users;  -- DELETES ALL DATA!
 CREATE TABLE users (..., email VARCHAR);

Alembic solution:

 ALTER TABLE users ADD COLUMN email VARCHAR;  -- Keeps existing data

--------------------------------------------------------------------------------------------------------------------------------

What is Alembic?

Definition: A database migration tool for SQLAlchemy.

What's a migration? A script that changes your database schema in a safe, reversible way.

--------------------------------------------------------------------------------------------------------------------------------

How Alembic Works

1. Install Alembic:

 pip install alembic
 alembic init alembic  # Creates alembic/ folder

2. Configure it (alembic/env.py):

 from models_db import Base
 target_metadata = Base.metadata  # Tell Alembic about your models

3. Create a migration:

 alembic revision --autogenerate -m "Add email to users"

Alembic generates:

 # alembic/versions/abc123_add_email_to_users.py

 def upgrade():
     """Add email column."""
     op.add_column('users', sa.Column('email', sa.String(), nullable=True))

 def downgrade():
     """Remove email column (rollback)."""
     op.drop_column('users', 'email')

4. Apply migration:

 alembic upgrade head  # Runs `upgrade()` function

What happens:

 1. Alembic connects to your database
 2. Checks alembic_version table (tracks current version)
 3. Runs upgrade() function
 4. Updates alembic_version to abc123

If something goes wrong:

 alembic downgrade -1  # Runs `downgrade()` function (undo last migration)

--------------------------------------------------------------------------------------------------------------------------------

Why You Don't Have Alembic (Yet)

Current setup:

 # main.py
 Base.metadata.create_all(bind=engine)  # Creates tables on startup

This is fine for development because:

 - You can delete kudos.db and start fresh
 - No production data to preserve

But in production:

 - ❌ create_all() doesn't add new columns to existing tables
 - ❌ You can't delete the database (you'd lose all kudos!)

Solution: Use Alembic for production deployments.

--------------------------------------------------------------------------------------------------------------------------------

Example: Adding Email Field with Alembic

Step 1: Update model (models_db.py):

 class User(Base):
     # ... existing fields
     email = Column(String, nullable=True)  # NEW

Step 2: Generate migration:

 alembic revision --autogenerate -m "Add email to users"

Generated file (alembic/versions/20240410_add_email.py):

 def upgrade():
     op.add_column('users', sa.Column('email', sa.String(), nullable=True))

 def downgrade():
     op.drop_column('users', 'email')

Step 3: Apply to database:

 alembic upgrade head

Result:

 - Existing users get email = NULL
 - New users can set email
 - No data lost!

--------------------------------------------------------------------------------------------------------------------------------

Interview Answer

"Alembic is a database migration tool that generates SQL scripts to update the schema without losing data. In my current setup, I
use Base.metadata.create_all() for simplicity, but for production, I'd add Alembic to handle schema changes safely. For example,
if I wanted to add an email field to users, Alembic would generate an ALTER TABLE migration that adds the column without dropping
existing data."

--------------------------------------------------------------------------------------------------------------------------------

8️⃣ ARCHITECTURE PATTERNS EXPLAINED

1. Layered Architecture (3-Tier)

 ┌─────────────────────────────────────┐
 │   HTTP Layer (routers/)             │  ← Handles HTTP requests/responses
 │   - auth.py: /register, /login      │
 │   - kudos.py: /kudos/add            │
 └─────────────────────────────────────┘
               ↓ (calls)
 ┌─────────────────────────────────────┐
 │   Service Layer (services/)         │  ← Business logic
 │   - auth_service.py                 │
 │   - kudos_service.py                │
 └─────────────────────────────────────┘
               ↓ (queries)
 ┌─────────────────────────────────────┐
 │   Data Layer (database.py, ORM)     │  ← Database access
 │   - models_db.py: User, KudosDB     │
 └─────────────────────────────────────┘

Why separate layers?

 - ✅ Testability: Test service layer without HTTP
 - ✅ Reusability: Both REST API and Slack commands call same services
 - ✅ Maintainability: Change database without touching HTTP code

--------------------------------------------------------------------------------------------------------------------------------

2. Dependency Injection

Without DI (manual dependencies):

 def register():
     db = SessionLocal()  # Create manually
     try:
         user = User(...)
         db.add(user)
         db.commit()
     finally:
         db.close()  # Remember to close!

With DI (FastAPI):

 def register(db: Session = Depends(get_db)):
     user = User(...)
     db.add(user)
     # Automatic commit and close

Benefits:

 - ✅ Less boilerplate
 - ✅ Automatic cleanup
 - ✅ Easy to mock in tests

--------------------------------------------------------------------------------------------------------------------------------

3. DTO Pattern (Data Transfer Objects)

Flow:

 HTTP Request (JSON)
     ↓ (Pydantic validates)
 Pydantic Model (UserCreate)
     ↓ (Service converts)
 SQLAlchemy Model (User)
     ↓ (Database saves)
 Database Row

Why separate Pydantic and SQLAlchemy models?

Pydantic (models.py):

 - Input validation (min length, max length)
 - Password exposed (for validation)
 - No database ID

SQLAlchemy (models_db.py):

 - Database schema (primary keys, foreign keys)
 - Password_hash (not plaintext)
 - Relationships (received_kudos, given_kudos)

Example:

Input (Pydantic):

 UserCreate(username="alice", password="pass1234")

Database (SQLAlchemy):

 User(
     id=1,
     username="alice",
     password_hash="$2b$12$Kix...",
     is_active=True,
     role="user",
     received_kudos=[...]
 )

--------------------------------------------------------------------------------------------------------------------------------

9️⃣ DATA FLOW EXAMPLES

Example 1: User Registration

 1. Client sends:
    POST /register
    {"username": "alice", "password": "pass1234"}

        ↓

 2. FastAPI receives request:
    - Parses JSON
    - Validates with UserCreate schema
      ✓ Username: 2-20 chars, alphanumeric
      ✓ Password: 4-30 chars, no spaces

        ↓

 3. routers/auth.py:
    def register(user: UserCreate, db: Session = Depends(get_db)):
        return auth_service.register_user(user, db)

        ↓

 4. services/auth_service.py:
    def register_user(user_data, db):
        # Check if username exists
        existing = db.query(User).filter(User.username == "alice").first()
        if existing:
            raise HTTPException(400, "Username exists")

        # Hash password
        hashed = hash_password("pass1234")

        # Create user
        new_user = User(username="alice", password_hash=hashed, ...)
        db.add(new_user)

        return {"status": "created"}

        ↓

 5. core/dependencies.py (get_db):
    finally:
        db.commit()  # Save to database
        db.close()   # Close connection

        ↓

 6. Response:
    {"status": "created"}

--------------------------------------------------------------------------------------------------------------------------------

Example 2: Sending Kudos via Slack

 1. User types in Slack:
    /kudos @alice Great job on the presentation!

        ↓

 2. Slack sends to your server:
    POST /slack/command
    Headers:
      X-Slack-Signature: v0=a2114d57b48eac39b9ad189dd8316235a7b4a8d21a10bd27519666489c69b503
      X-Slack-Request-Timestamp: 1716842400
    Body (form-encoded):
      token=abc123&user_id=U12345&user_name=bob&text=@alice Great job!

        ↓

 3. routers/slack.py:
    @router.post("/command")
    async def handle_slack_command(request: Request, form: Form(...)):
        # Verify HMAC signature
        await verify_slack_signature(request)

        # Parse command
        result = handle_command(form, db)
        return result

        ↓

 4. services/slack_service.py:
    def handle_command(form, db):
        text = form.get("text")  # "@alice Great job!"
        from_username = form.get("user_name")  # "bob"

        # Parse: @alice → "alice", "Great job!" → message
        to_user, message = parse_kudos_command(text)

        # Call kudos service
        kudos_service.add_kudos(to_user, message, from_user, db)

        # Format Slack response
        return format_slack_response(f"Kudos sent to @{to_user}!")

        ↓

 5. services/kudos_service.py:
    def add_kudos(to_user, message, from_user, db):
        # 1. Validate users exist
        sender = db.query(User).filter(User.username == from_user).first()
        receiver = db.query(User).filter(User.username == to_user).first()

        # 2. Check daily limit
        today_count = db.query(KudosDB).filter(
            KudosDB.from_user_id == sender.id,
            KudosDB.time_created >= start_of_day
        ).count()
        if today_count >= 5:
            raise HTTPException(400, "Too many kudos today")

        # 3. Prevent self-kudos
        if sender.id == receiver.id:
            raise HTTPException(400, "Cannot give kudos to yourself")

        # 4. Create kudos
        kudos = KudosDB(
            from_user_id=sender.id,
            to_user_id=receiver.id,
            message=message,
            time_created=datetime.now()
        )
        db.add(kudos)

        logger.info(f"{from_user} gave kudos to {to_user}")

        ↓

 6. Slack receives response:
    {
      "response_type": "in_channel",
      "text": "Kudos sent to @alice!"
    }

        ↓

 7. Slack displays in channel:
    [Bot] Kudos sent to @alice!

--------------------------------------------------------------------------------------------------------------------------------

🔟 INTERVIEW ANSWERS - QUICK REFERENCE

Q: Why FastAPI over Flask/Django?

"FastAPI provides automatic API documentation via Swagger, built-in dependency injection, and native async support. For a
microservice like a Slack bot, I didn't need Django's full web framework (templates, admin panel, ORM). Flask would work, but
FastAPI's automatic validation and docs saved development time."

--------------------------------------------------------------------------------------------------------------------------------

Q: Why SQLite? What are the disadvantages?

"I used SQLite for rapid development because it requires zero configuration—just a file. The main disadvantage is write
concurrency: SQLite locks the entire database on write, so concurrent requests queue up. For production with high traffic, I'd
migrate to PostgreSQL using the same SQLAlchemy code. PostgreSQL offers row-level locking, better concurrency, and richer data
types."

Specific disadvantages:

 1. Write locks: Only one write at a time (blocks concurrent requests)
 2. No network access: Must be on same machine (can't use managed DB services)
 3. Limited ALTER TABLE: Can't rename columns easily (makes migrations harder)
 4. Type system: No native UUID, JSON types (PostgreSQL has these)

--------------------------------------------------------------------------------------------------------------------------------

Q: What is Alembic? Why don't you use it?

"Alembic is a database migration tool for SQLAlchemy. It generates scripts to alter the schema without losing data. For example,
if I add an email field to users, Alembic creates an ALTER TABLE migration instead of dropping the table. I don't currently use
it because I'm in development mode with Base.metadata.create_all(), but for production, I'd add Alembic to safely evolve the
schema."

--------------------------------------------------------------------------------------------------------------------------------

Q: Explain JWT authentication

"JWT (JSON Web Token) is a stateless authentication system. When a user logs in, I create a token containing their username and
expiration time, signed with a secret key. The user includes this token in the Authorization header for future requests. I verify
the signature and check expiration without querying the database."

Benefits:

 - Stateless (no session table)
 - Scalable (works across multiple servers)
 - Mobile-friendly (standard header format)

Trade-offs:

 - Can't revoke instantly (token valid until expiration)
 - Larger than session IDs (~200 bytes vs ~20 bytes)

Mitigation:

 - Short expiration (60 minutes)
 - Could add token blacklist if needed

--------------------------------------------------------------------------------------------------------------------------------

Q: Why separate Pydantic and SQLAlchemy models?

"Pydantic models validate API input/output, while SQLAlchemy models define database schema. For example, UserCreate has a
plaintext password for validation, but the User table stores password_hash. This separation keeps validation logic out of the ORM
and makes the API contract explicit."

--------------------------------------------------------------------------------------------------------------------------------

Q: Explain your layered architecture

"I use a 3-layer architecture: Routers (HTTP layer), Services (business logic), and Data layer (ORM). Routers are thin—they just
parse requests and call services. Services contain all business rules (daily kudos limits, validation). This makes services
reusable (both REST API and Slack commands call the same service) and easy to test (mock the database, no HTTP needed)."

--------------------------------------------------------------------------------------------------------------------------------

Q: Why bcrypt for passwords?

"Bcrypt is designed to be slow (~100ms per hash) to prevent brute-force attacks. It automatically salts each password, so
identical passwords have different hashes. This protects against rainbow table attacks. I use passlib which provides a simple
interface and follows security best practices."

--------------------------------------------------------------------------------------------------------------------------------

Q: How do you test the database?

"I use pytest with an in-memory SQLite database (:memory:). Each test gets a fresh database via a fixture. This is fast (no disk
I/O) and isolated (tests don't affect each other). After the test, the database is destroyed automatically."

--------------------------------------------------------------------------------------------------------------------------------

📊 COMPLETE TECH STACK SUMMARY

┌──────────────────────┬──────────────────────┬──────────────────────┬───────────────────┐
│ Component            │ Technology           │ Why Chosen           │ Alternative       │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Web Framework        │ FastAPI              │ Auto-docs, DI, async │ Flask, Django     │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ ASGI Server          │ Uvicorn              │ Async support        │ Gunicorn          │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Database             │ SQLite               │ Zero config          │ PostgreSQL        │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ ORM                  │ SQLAlchemy 2.0       │ Database abstraction │ Django ORM        │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Password Hashing     │ bcrypt (via passlib) │ Industry standard    │ Argon2            │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ JWT Tokens           │ python-jose          │ Stateless auth       │ sessions          │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Validation           │ Pydantic             │ Type-safe            │ manual validation │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Config               │ pydantic-settings    │ Type-safe env vars   │ os.environ        │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Testing              │ pytest               │ Simple, powerful     │ unittest          │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Logging              │ RotatingFileHandler  │ Prevent log bloat    │ syslog            │
├──────────────────────┼──────────────────────┼──────────────────────┼───────────────────┤
│ Containerization     │ Docker               │ Portable deployment  │ Virtual machines  │
└──────────────────────┴──────────────────────┴──────────────────────┴───────────────────┘

--------------------------------------------------------------------------------------------------------------------------------

🎯 KEY TAKEAWAYS FOR INTERVIEWS

 1. Every choice has trade-offs: SQLite is fast to setup but limited concurrency; JWT is stateless but can't revoke instantly.
 2. Show migration paths: "I can switch from SQLite to PostgreSQL by changing one line thanks to SQLAlchemy."
 3. Explain real-world impact: "bcrypt's slow hashing prevents brute-force attacks even if the database is leaked."
 4. Mention production improvements: "For production, I'd add Alembic for migrations, switch to PostgreSQL, and implement token
blacklisting."
 5. Understand the "why": Don't just say "I used FastAPI." Say "FastAPI's automatic documentation and dependency injection
reduced boilerplate code."

--------------------------------------------------------------------------------------------------------------------------------

This is the complete analysis! You now have beginner-friendly explanations for every library, file, and architectural decision.
Good luck with your interviews! 🚀

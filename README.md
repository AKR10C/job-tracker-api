# Job Application Tracker API

A FastAPI-based REST API for tracking job applications with user authentication, database persistence, and JWT-based authorization.

---

## 🏗️ Project Structure Overview

```
job-tracker-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main application & route handlers
│   ├── auth.py              # Authentication & JWT logic
│   ├── database.py          # Database configuration & session management
│   ├── models.py            # SQLAlchemy ORM models
│   └── schemas.py           # Pydantic validation schemas
├── requirements.txt         # Python dependencies
└── README.md               # Documentation
```

---

## 🔧 How It Works - Deep Dive

### 1. **Application Entry Point** (`main.py`)

#### Route Architecture:
- `POST /register` - User registration endpoint
- `POST /login` - User authentication & token generation
- `POST /jobs` - Add a new job application
- `GET /jobs` - Retrieve user's job applications

#### Key Components:

```python
models.Base.metadata.create_all(bind=engine)
```
- **Purpose**: Automatically creates database tables on startup
- **Why**: Ensures database schema exists before API operations
- **Alternative**: Manual migration tools (Alembic) for production environments

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
- **What's happening**: Dependency injection pattern for database sessions
- **Why this matters**:
  - ✅ Ensures session is created for each request
  - ✅ Automatically closes session (no resource leaks)
  - ✅ Uses `yield` instead of `return` for proper cleanup
- **Syntax explanation**: Generator function pattern in FastAPI
  - Code before `yield` runs before request
  - Code after `yield` runs after request completes
  - This is FastAPI's teardown pattern (like context managers)

### 2. **Authentication Module** (`auth.py`)

#### Password Hashing:
```python
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
```
- **Algorithm**: PBKDF2 with SHA256
- **Why PBKDF2?**
  - ✅ Industry standard for password hashing
  - ✅ Slow computation (resistant to brute-force)
  - ✅ Built into passlib library
- **Alternative approaches**:
  - `bcrypt`: More modern, but slower (if performance matters)
  - `argon2`: Best-in-class, but requires additional dependencies
  - ❌ NOT plain hashing/MD5 (security risk)

#### JWT Token Generation:
```python
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```
- **What's happening**: 
  1. Copy data to avoid mutations
  2. Add expiration time (30 minutes)
  3. Encode as JWT with secret key
- **Why JWT?**
  - ✅ Stateless (no server-side session storage needed)
  - ✅ Self-contained (token has all info)
  - ✅ Standard for REST APIs
- **Why 30 minutes?**
  - ✅ Security: Limits exposure if token is stolen
  - ✅ Usability: Refreshes aren't too frequent
  - Alternative: 24 hours (less secure but more convenient)

#### Token Validation:
```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int | None = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```
- **Type hint** `int | None`: Python 3.10+ union syntax (alternative: `Optional[int]`)
- **JWTError catch**: Handles tampering, expiration, invalid signatures
- **Why dependency injection?**: FastAPI automatically extracts & validates tokens

### 3. **Database Configuration** (`database.py`)

```python
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

#### Why these settings?
- **`autocommit=False`**: Explicit control over transaction boundaries
  - Allows batch operations before committing
  - Rollback on error
- **`autoflush=False`**: Prevents automatic writes during queries
  - Avoids side effects
  - Better performance
- **`create_engine()`**: Connection pooling
  - Reuses database connections (expensive to create)
  - Configurable pool size

#### Alternative: Raw SQL
```python
# ❌ NOT recommended
import sqlite3
conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()
```
Why we don't do this:
- No connection pooling
- SQL injection vulnerabilities
- Manual transaction management
- No relationship handling

### 4. **Database Models** (`models.py`)

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(225))
```

#### Why SQLAlchemy ORM?
- ✅ Type-safe relationships
- ✅ Automatic SQL generation
- ✅ Built-in validation
- ✅ Easy migrations (with Alembic)

#### Design Decisions:

| Decision | Why | Alternative |
|----------|-----|-------------|
| `unique=True` on email | Prevents duplicate accounts | Check in code (error-prone) |
| `index=True` on email | Fast lookups on login | No index (slow queries) |
| `String(225)` for password | Hash is ~60-72 chars, buffer for future | `String(255)` (wastes space) |
| Integer `id` as PK | Standard, auto-increment | UUID (more secure, complex) |
| Separate User & job tables | Data normalization | Single table (data duplication) |

#### Foreign Key:
```python
user_id = Column(Integer, ForeignKey("users.id"))
```
- Creates relationship between job and user
- **Why enforce at database level?**
  - ✅ Prevents orphaned records
  - ✅ Referential integrity
  - ✅ Performance (indexes)

### 5. **Pydantic Schemas** (`schemas.py`)

```python
class UserCreate(BaseModel):
    email: str
    password: str
```

#### Why Pydantic NOT just use models?
- **Input validation** (schemas):
  ```python
  # Schemas validate request data
  email: str  # Must be string
  password: str  # Must be string
  ```
- **Database models** (SQLAlchemy):
  ```python
  # Models define table structure
  id = Column(Integer, primary_key=True)
  ```

#### Benefits of separation:
1. **Validation**: Pydantic validates before database
2. **Security**: Hide internal fields (don't expose `id`)
3. **Flexibility**: Different input/output schemas
4. **Documentation**: Auto-generated OpenAPI docs

#### Alternative: Single model class
```python
# ❌ NOT recommended
class User(Base):
    # Problem: Exposes internal fields like `id`, `created_at`
    # Security: Cannot selectively expose fields
    # Validation: Mixing concerns
```

---

## 🔑 Key Design Patterns Used

### 1. **Dependency Injection**
```python
def add_job(
    job: schemas.JobCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
```
- **Benefits**:
  - ✅ Testable (inject mock database)
  - ✅ Reusable (same auth logic everywhere)
  - ✅ Decoupled (handlers don't know about DB/auth)

### 2. **Repository Pattern** (implicit)
- `get_db()` is a repository of database sessions
- Separates data access from business logic

### 3. **Factory Pattern**
- `SessionLocal()` creates session instances
- `create_engine()` creates database connections

---

## 🚀 API Endpoint Walkthrough

### **POST /register**
```python
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed = auth.hash_password(user.password)
    db_user = models.User(email=user.email, password=hashed)
    db.add(db_user)
    db.commit()
    return {"message":"User registered succesfully"}
```

**Flow**:
1. User sends `{email: "user@test.com", password: "secret"}`
2. Pydantic validates input
3. Password hashed using PBKDF2
4. User record created in database
5. Transaction committed

**Missing**: Error handling for duplicate email

### **POST /login**
```python
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user or not auth.verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}
```

**Flow**:
1. Parse username/password from form
2. Query database for user
3. Compare passwords (hashed comparison)
4. Generate JWT token
5. Return token

**Why `OAuth2PasswordRequestForm`?**
- Standard form format (email/password in body)
- Automatic parsing
- Security headers

### **POST /jobs**
```python
@app.post("/jobs")
def add_job(
    job: schemas.JobCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_job = models.job(**job.dict(), user_id=user_id)
    db.add(new_job)
    db.commit()
    return {"message": "Job added successfully"}
```

**Key detail**: `**job.dict()`
- Unpacks schema dict into model kwargs
- Alternative: `new_job = models.job(title=job.title, company=job.company, ...)`
- Why unpacking? Less repetition, scalable

### **GET /jobs**
```python
@app.get("/jobs")
def get_jobs(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.job).filter(models.job.user_id == user_id).all()
```

**Query breakdown**:
- `db.query()` - Create query builder
- `.filter()` - WHERE clause
- `.all()` - Execute and return all results

---

## 🐛 Known Issues & Improvements

### Critical Issues:

|             Issue                 |    Risk   |               Fix            |
|-----------------------------------|-----------|------------------------------|
| Hardcoded `SECRET_KEY`            | ⚠️ HIGH   | Use environment variable     |
| No input validation               | ⚠️ MEDIUM | Add length/format checks     |
| No error handling for duplicates  | ⚠️ MEDIUM | Catch IntegrityError         |
| Case-sensitive email              | ⚠️ LOW    | Normalize to lowercase       |
| No password strength requirements | ⚠️ MEDIUM | Validate minimum complexity  |
| Class name `job` (lowercase)      | ⚠️ LOW    | Rename to `Job` (PEP 8)      |

### Recommended Improvements:

```python
# ✅ Environment-based secrets
from dotenv import load_dotenv
SECRET_KEY = os.getenv("SECRET_KEY")

# ✅ Email validation
from pydantic import EmailStr
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# ✅ Duplicate email handling
try:
    db.add(db_user)
    db.commit()
except IntegrityError:
    raise HTTPException(status_code=400, detail="Email already exists")

# ✅ Password validation
import re
def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain uppercase letter")
```

---

## 📚 Why This Architecture - Interview Explanation

### Question: "Why did you use FastAPI?"
**Answer**:
- **Speed**: Built on Starlette, async support for concurrent requests
- **Type hints**: Full type safety with Pydantic
- **Auto documentation**: Automatic OpenAPI/Swagger docs
- **Dependency injection**: Clean testable code
- **Alternatives**: Flask (lightweight but manual), Django (heavy but batteries-included)

### Question: "Why SQLAlchemy ORM?"
**Answer**:
- **Database agnostic**: Works with PostgreSQL, MySQL, SQLite
- **Relationships**: Handles foreign keys automatically
- **Security**: Prevents SQL injection via parameterized queries
- **Alternatives**: Raw SQL (unsafe), Django ORM (tied to Django)

### Question: "Why JWT tokens instead of sessions?"
**Answer**:
- **Stateless**: No server-side storage needed (scales horizontally)
- **Distributed**: Works across multiple servers
- **Mobile-friendly**: Tokens work with mobile apps
- **Self-contained**: User info embedded in token
- **Trade-off**: Token revocation is harder (need blacklist)

### Question: "Why separate schemas and models?"
**Answer**:
- **Validation**: Schemas validate input, models define database structure
- **Security**: Hide internal fields (don't expose `id` in API responses)
- **Flexibility**: Different input/output formats
- **Best practice**: Clean separation of concerns

### Question: "How does dependency injection work here?"
**Answer**:
```python
# FastAPI automatically calls get_db() before each request
# Injects result into function parameter
@app.post("/jobs")
def add_job(db: Session = Depends(get_db)):
    # db is automatically provided
    pass
```
- **Benefits**: Testable (inject mock), reusable, decoupled
- **Implementation**: FastAPI calls dependency functions automatically

---

## 🧪 Testing Strategy (Interview Topics)

### Unit Tests:
```python
# Test password hashing
def test_hash_password():
    pwd = "secret123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert hashed != pwd  # Not stored plaintext
```

### Integration Tests:
```python
# Test full flow: register -> login -> create job
def test_register_and_login():
    # Register user
    response = client.post("/register", json={
        "email": "test@test.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    
    # Login
    response = client.post("/login", data={
        "username": "test@test.com",
        "password": "secret123"
    })
    assert "access_token" in response.json()
```

---

## 🔒 Security Best Practices Used

|       Practice       | Implementation  |         Why             |
|----------------------|-----------------|-------------------------|
| Password hashing     | PBKDF2-SHA256   | Never store plaintext   |
| JWT signatures       | HS256 algorithm | Prevents tampering      |
| Token expiration     | 30 minutes      | Limits exposure window  |
| Unique constraints   | Database level  | Prevents duplicates     |
| Dependency injection | FastAPI Depends | Enforces auth on routes |

---

## 🚢 Deployment Considerations

### Production Checklist:
- [ ] Move `SECRET_KEY` to environment variable
- [ ] Add proper error handling & logging
- [ ] Use database migrations (Alembic)
- [ ] Enable CORS if frontend is separate domain
- [ ] Set up HTTPS/SSL
- [ ] Add rate limiting
- [ ] Use connection pooling for database
- [ ] Add input validation & sanitization
- [ ] Set up monitoring & alerting

### Example production setup:
```python
# .env file
DATABASE_URL=postgresql://user:pass@prod-db:5432/jobtracker
SECRET_KEY=<long-random-key-from-secrets-manager>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---


---

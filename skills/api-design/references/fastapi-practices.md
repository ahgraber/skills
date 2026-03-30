# FastAPI Best Practices

This reference covers FastAPI-specific patterns.
For general API design principles (URI naming, versioning, error handling, pagination), see the other references in this skill.

## Project Structure

### Domain-driven organization (recommended for non-trivial apps)

```text
src/
├── auth/
│   ├── router.py           # FastAPI router with endpoints
│   ├── schemas.py           # Pydantic request/response models
│   ├── models.py            # SQLAlchemy/DB models
│   ├── dependencies.py      # FastAPI dependencies
│   ├── service.py           # Business logic
│   ├── constants.py
│   ├── config.py            # Module-specific settings
│   └── exceptions.py        # Domain exceptions
├── orders/
│   ├── router.py
│   ├── schemas.py
│   ├── ...
├── config.py                # Global config
├── database.py              # DB connection setup
├── exceptions.py            # Global exception handlers
├── pagination.py            # Shared pagination utilities
└── main.py                  # App factory
```

When importing across domains, use explicit module names to avoid ambiguity:

```python
from src.auth import constants as auth_constants
from src.notifications import service as notification_service
```

### Layer-based organization (acceptable for small apps)

```text
app/
├── api/routes/              # All routers
├── core/                    # Config, security, DB
├── crud.py                  # All CRUD operations
├── models.py                # All DB models
└── main.py
```

Switch to domain-driven when you outgrow this.

## Async vs Sync — The Critical Distinction

This is FastAPI's most common footgun.
Get this wrong and you freeze the entire server.

### The rule

- **`async def`**: Use ONLY when the body contains `await` calls to async libraries
- **`def`** (plain function): Use when calling blocking/synchronous code — FastAPI automatically runs it in a threadpool
- **Never** put blocking calls inside `async def` — this blocks the entire event loop

```python
# WRONG — blocks the event loop, freezes all concurrent requests
@router.get("/bad")
async def bad_endpoint():
    time.sleep(10)  # blocking call in async context
    result = requests.get(url)  # blocking HTTP call in async context
    return result


# CORRECT — FastAPI runs this in a threadpool automatically
@router.get("/sync-ok")
def sync_endpoint():
    time.sleep(10)  # blocking, but runs in thread
    return {"ok": True}


# CORRECT — truly async with non-blocking calls
@router.get("/async-ok")
async def async_endpoint():
    await asyncio.sleep(10)  # non-blocking
    async with httpx.AsyncClient() as client:
        result = await client.get(url)  # non-blocking
    return result
```

For **CPU-intensive** work (image processing, ML inference, heavy computation): offload to a process pool or task queue (Celery, ARQ), not threads (GIL prevents real parallelism).

## Dependencies for Validation and Auth

FastAPI dependencies are the primary tool for request validation, authorization, and shared logic.
Use them extensively.

### Resource validation

```python
async def valid_post_id(post_id: UUID4) -> Post:
    post = await post_service.get_by_id(post_id)
    if not post:
        raise PostNotFound()
    return post


@router.get("/posts/{post_id}")
async def get_post(post: Post = Depends(valid_post_id)):
    return post


@router.patch("/posts/{post_id}")
async def update_post(
    update: PostUpdate,
    post: Post = Depends(valid_post_id),
):
    return await post_service.update(post, update)
```

### Chained dependencies for authorization

```python
async def valid_owned_post(
    post: Post = Depends(valid_post_id),
    user: User = Depends(get_current_user),
) -> Post:
    if post.author_id != user.id:
        raise ForbiddenError()
    return post


@router.delete("/posts/{post_id}")
async def delete_post(post: Post = Depends(valid_owned_post)):
    await post_service.delete(post)
```

FastAPI **caches dependency results within a request** — if `get_current_user` appears in multiple dependency chains, it executes only once per request.

## Pydantic Patterns

### Use Field constraints aggressively

```python
from pydantic import BaseModel, Field, EmailStr


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=150)
    role: UserRole = UserRole.MEMBER

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "alice@example.com", "name": "Alice", "age": 30}]}
    )
```

### Separate request and response models

```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    created_at: datetime
    # Note: no password field


class UserListResponse(BaseModel):
    id: UUID
    name: str
    # Fewer fields for list views
```

Never return the same model for create, read, and list.
Response models control what leaves the API boundary.

### Custom base model for app-wide behavior

```python
class AppBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # ORM mode
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )
```

## Error Handling

### Domain exceptions, not HTTPException in services

Service and data layers should not know about HTTP.
Define domain exceptions and map them at the API layer:

```python
# Domain exceptions (in exceptions.py)
class DomainError(Exception):
    pass


class PostNotFound(DomainError):
    pass


class DuplicateEmail(DomainError):
    pass


# Exception handlers (in main.py or exceptions.py)
@app.exception_handler(PostNotFound)
async def post_not_found_handler(request: Request, exc: PostNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "type": "https://api.example.com/errors/not-found",
            "title": "Not Found",
            "status": 404,
            "detail": str(exc),
        },
    )


@app.exception_handler(DuplicateEmail)
async def duplicate_email_handler(request: Request, exc: DuplicateEmail):
    return JSONResponse(
        status_code=409,
        content={
            "type": "https://api.example.com/errors/conflict",
            "title": "Conflict",
            "status": 409,
            "detail": str(exc),
        },
    )
```

### Document error responses in endpoints

FastAPI doesn't auto-document custom exception handlers.
Add them explicitly:

```python
@router.get(
    "/posts/{post_id}",
    responses={
        404: {"description": "Post not found"},
        403: {"description": "Not authorized to view this post"},
    },
)
async def get_post(post: Post = Depends(valid_post_id)):
    return post
```

## Configuration

### Split settings by domain

```python
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")
    host: str = "localhost"
    port: int = 5432
    name: str = "app"


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_")
    secret_key: str
    token_expiry_minutes: int = 30


class AppConfig(BaseSettings):
    debug: bool = False
    db: DatabaseConfig = DatabaseConfig()
    auth: AuthConfig = AuthConfig()
```

## Testing

### Async test client from day 0

```python
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_create_user(client: AsyncClient):
    response = await client.post("/users", json={"email": "test@example.com", "name": "Test"})
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

### Dependency overrides for isolation

```python
def get_test_db():
    return test_database_session


app.dependency_overrides[get_database] = get_test_db
```

## Router Organization

### Use `APIRouter` with consistent prefixes and tags

```python
# auth/router.py
router = APIRouter(prefix="/auth", tags=["Authentication"])

# orders/router.py
router = APIRouter(prefix="/orders", tags=["Orders"])

# main.py
app.include_router(auth_router)
app.include_router(orders_router, prefix="/v1")
```

### Response model declarations

```python
@router.get("/users", response_model=list[UserResponse])
async def list_users(): ...


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: CreateUserRequest): ...
```

Always set `response_model` — it controls serialization, filters out fields not in the model, and drives OpenAPI documentation.

## Common Footguns

| Footgun                                          | Prevention                                                                         |
| ------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Blocking call in `async def`                     | Use `def` for sync code; `async def` only with `await`                             |
| `ValueError` becoming Pydantic `ValidationError` | Be aware that `ValueError` in `@field_validator` is caught and wrapped by Pydantic |
| Missing `response_model` leaking internal fields | Always declare `response_model` on endpoints                                       |
| Global database sessions                         | Use dependency injection for DB sessions; never share across requests              |
| `HTTPException` in service layer                 | Use domain exceptions + exception handlers                                         |
| No async test client                             | Set up `httpx.AsyncClient` with `ASGITransport` from the start                     |

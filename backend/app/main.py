from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Literal

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Task, User
from .security import create_token, decode_token, hash_password, verify_password


class ApiInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginInput(ApiInput):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TaskInput(ApiInput):
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=1000)
    status: Literal["todo", "doing", "done"] = "todo"
    priority: Literal["low", "medium", "high"] = "medium"


class TaskPatch(ApiInput):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    status: Literal["todo", "doing", "done"] | None = None
    priority: Literal["low", "medium", "high"] | None = None


class TaskOutput(TaskInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    created_at: datetime


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Db = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: Db
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def visible_task(task_id: int, user: User, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None or (user.role != "admin" and task.owner_id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def seed_demo_data() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "demo_admin"))
        if user is None:
            user = User(username="demo_admin", password_hash=hash_password("Demo123!"), role="admin")
            db.add(user)
            db.flush()
            db.add_all(
                [
                    Task(title="مراجعة تجربة الجوال", description="التحقق من الواجهة العربية", status="doing", priority="high", owner_id=user.id),
                    Task(title="توثيق واجهة API", description="إضافة أمثلة الطلبات والاستجابات", status="todo", priority="medium", owner_id=user.id),
                    Task(title="تشغيل اختبارات التكامل", description="PostgreSQL + FastAPI", status="done", priority="high", owner_id=user.id),
                ]
            )
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    seed_demo_data()
    yield


app = FastAPI(title="Secure TaskFlow API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenOutput)
def login(data: LoginInput, db: Db) -> TokenOutput:
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenOutput(access_token=create_token(user.id, user.role))


@app.get("/tasks", response_model=list[TaskOutput])
def list_tasks(user: CurrentUser, db: Db) -> list[Task]:
    query = select(Task).order_by(Task.created_at.desc())
    if user.role != "admin":
        query = query.where(Task.owner_id == user.id)
    return list(db.scalars(query))


@app.post("/tasks", response_model=TaskOutput, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskInput, user: CurrentUser, db: Db) -> Task:
    task = Task(**data.model_dump(), owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOutput)
def update_task(task_id: int, data: TaskPatch, user: CurrentUser, db: Db) -> Task:
    task = visible_task(task_id, user, db)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: CurrentUser, db: Db) -> None:
    task = visible_task(task_id, user, db)
    db.delete(task)
    db.commit()


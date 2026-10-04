import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from database import (
    create_table,
    create_user,
    get_user_by_username,
    get_all_todos,
    create_todo,
    get_todo,
    update_todo,
    delete_todo
)


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


create_table()


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-secret-key-change-this-in-production"
)

ALGORITHM = "HS256"

security = HTTPBearer()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class Todo(BaseModel):
    title: str
    completed: bool


def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120000
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (ValueError, TypeError):
        return False


def create_access_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(days=7)

    payload = {
        "user_id": user_id,
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_user_by_id(user_id):
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, username
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    return user


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Geçersiz token."
            )

        return int(user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Oturumunuz sona erdi. Tekrar giriş yapın."
        )

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Geçersiz token."
        )


@app.get("/")
def ana_sayfa():
    return {
        "mesaj": "To-Do API çalışıyor!"
    }


@app.post("/auth/register")
def register(data: RegisterRequest):

    username = data.username.strip()
    password = data.password

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Kullanıcı adı en az 3 karakter olmalı."
        )

    if len(username) > 50:
        raise HTTPException(
            status_code=400,
            detail="Kullanıcı adı en fazla 50 karakter olabilir."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Şifre en az 6 karakter olmalı."
        )

    if len(password) > 128:
        raise HTTPException(
            status_code=400,
            detail="Şifre en fazla 128 karakter olabilir."
        )

    password_hash = hash_password(password)

    user_id = create_user(
        username,
        password_hash
    )

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Bu kullanıcı adı zaten kullanılıyor."
        )

    token = create_access_token(user_id)

    return {
        "token": token,
        "username": username
    }


@app.post("/auth/login")
def login(data: LoginRequest):

    username = data.username.strip()

    user = get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    user_id = user[0]
    stored_password_hash = user[2]

    if not verify_password(
        data.password,
        stored_password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    token = create_access_token(user_id)

    return {
        "token": token,
        "username": user[1]
    }


@app.get("/me")
def get_me(
    user_id: int = Depends(get_current_user_id)
):
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Kullanıcı bulunamadı."
        )

    return {
        "id": user[0],
        "username": user[1]
    }


@app.post("/todos")
def create_todo_api(
    todo: Todo,
    user_id: int = Depends(get_current_user_id)
):
    todo_id = create_todo(
        todo.title,
        todo.completed,
        user_id
    )

    return {
        "id": todo_id,
        "title": todo.title,
        "completed": todo.completed
    }


@app.get("/todos")
def get_todos(
    user_id: int = Depends(get_current_user_id)
):
    todos = get_all_todos(user_id)

    return [
        {
            "id": todo[0],
            "title": todo[1],
            "completed": bool(todo[2])
        }
        for todo in todos
    ]


@app.get("/todos/{todo_id}")
def get_todo_api(
    todo_id: int,
    user_id: int = Depends(get_current_user_id)
):
    todo = get_todo(
        todo_id,
        user_id
    )

    if not todo:
        raise HTTPException(
            status_code=404,
            detail="To-Do bulunamadı"
        )

    return {
        "id": todo[0],
        "title": todo[1],
        "completed": bool(todo[2])
    }


@app.put("/todos/{todo_id}")
def update_todo_api(
    todo_id: int,
    todo: Todo,
    user_id: int = Depends(get_current_user_id)
):
    updated_todo = update_todo(
        todo_id,
        todo.title,
        todo.completed,
        user_id
    )

    if not updated_todo:
        raise HTTPException(
            status_code=404,
            detail="To-Do bulunamadı"
        )

    return {
        "id": updated_todo[0],
        "title": updated_todo[1],
        "completed": bool(updated_todo[2])
    }


@app.delete("/todos/{todo_id}")
def delete_todo_api(
    todo_id: int,
    user_id: int = Depends(get_current_user_id)
):
    deleted = delete_todo(
        todo_id,
        user_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="To-Do bulunamadı"
        )

    return {
        "mesaj": "To-Do silindi"
    }
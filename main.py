import os
import hashlib
from uuid import uuid4
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Falta configurar DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


app = FastAPI(
    title="Mini Marketplace Cloud - Identidad, Usuarios y Sesiones",
    version="1.0.0",
    description="Primera versión funcional con Supabase"
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "customer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ValidateRequest(BaseModel):
    access_token: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


@app.get("/")
def root():
    return {
        "service": "Identity Service",
        "status": "running",
        "database": "Supabase PostgreSQL"
    }


@app.post("/auth/register", status_code=201)
def register(data: RegisterRequest):
    db = SessionLocal()

    try:
        existing_user = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": data.email}
        ).fetchone()

        if existing_user:
            raise HTTPException(status_code=409, detail="El email ya está registrado")

        user_id = str(uuid4())
        password_hash = hash_password(data.password)

        db.execute(
            text("""
                INSERT INTO users (id, name, email, password_hash, role, active)
                VALUES (:id, :name, :email, :password_hash, :role, true)
            """),
            {
                "id": user_id,
                "name": data.name,
                "email": data.email,
                "password_hash": password_hash,
                "role": data.role
            }
        )

        db.commit()

        return {
            "access_token": "jwt-demo-token",
            "refresh_token": "refresh-demo-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {
                "id": user_id,
                "name": data.name,
                "email": data.email,
                "roles": [data.role],
                "active": True
            }
        }

    finally:
        db.close()


@app.post("/auth/login")
def login(data: LoginRequest):
    db = SessionLocal()

    try:
        user = db.execute(
            text("""
                SELECT id, name, email, password_hash, role, active
                FROM users
                WHERE email = :email
            """),
            {"email": data.email}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        return {
            "access_token": "jwt-demo-token",
            "refresh_token": "refresh-demo-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "roles": [user.role],
                "active": user.active
            }
        }

    finally:
        db.close()


@app.post("/auth/logout", status_code=204)
def logout():
    return


@app.post("/auth/validate")
def validate(data: ValidateRequest):
    if data.access_token != "jwt-demo-token":
        raise HTTPException(status_code=401, detail="Token inválido")

    return {
        "valid": True,
        "message": "Token válido"
    }


@app.get("/users")
def list_users():
    db = SessionLocal()

    try:
        users = db.execute(
            text("""
                SELECT id, name, email, role, active
                FROM users
                ORDER BY created_at DESC
            """)
        ).fetchall()

        return {
            "total": len(users),
            "users": [
                {
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "roles": [user.role],
                    "active": user.active
                }
                for user in users
            ]
        }

    finally:
        db.close()


@app.get("/users/{user_id}")
def get_user(user_id: str):
    db = SessionLocal()

    try:
        user = db.execute(
            text("""
                SELECT id, name, email, role, active
                FROM users
                WHERE id = :id
            """),
            {"id": user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "roles": [user.role],
            "active": user.active
        }

    finally:
        db.close()


@app.put("/users/{user_id}")
def update_user(user_id: str, data: UpdateProfileRequest):
    db = SessionLocal()

    try:
        user = db.execute(
            text("SELECT id FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if data.name:
            db.execute(
                text("UPDATE users SET name = :name WHERE id = :id"),
                {"name": data.name, "id": user_id}
            )

        db.commit()

        return {
            "message": "Usuario actualizado correctamente"
        }

    finally:
        db.close()


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    db = SessionLocal()

    try:
        db.execute(
            text("DELETE FROM users WHERE id = :id"),
            {"id": user_id}
        )

        db.commit()
        return

    finally:
        db.close()


@app.get("/identity/roles")
def list_roles():
    return [
        {"name": "guest", "description": "Invitado", "permissions": []},
        {"name": "customer", "description": "Cliente", "permissions": ["orders:read"]},
        {"name": "seller", "description": "Vendedor", "permissions": ["products:create", "products:edit"]},
        {"name": "admin", "description": "Administrador", "permissions": ["*"]}
    ]


@app.get("/identity/permissions")
def list_permissions():
    return [
        {"name": "orders:read", "description": "Consultar pedidos"},
        {"name": "products:create", "description": "Crear productos"},
        {"name": "products:edit", "description": "Editar productos"}
    ]

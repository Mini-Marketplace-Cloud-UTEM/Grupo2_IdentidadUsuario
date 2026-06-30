import os
import hashlib
from uuid import uuid4
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Falta configurar DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

session_tokens = {}

security = HTTPBearer()


app = FastAPI(
    title="Mini Marketplace Cloud - Identidad, Usuarios y Sesiones",
    version="1.0.0",
    description="versión funcional con Supabase"
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def issue_token(user_id: str):
    token = str(uuid4())
    session_tokens[token] = user_id
    return token


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


class DeleteUserRequest(BaseModel):
    current_password: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class AuthData(BaseModel):
    user_id: str
    roles: List[str]


@app.get("/")
def root():
    return {
        "service": "Identity Service",
        "status": "running",
        "database": "Supabase PostgreSQL",
        "version": "v2-httpbearer"
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
                "role": "customer"
            }
        )

        db.commit()

        access_token = issue_token(user_id)

        return {
            "access_token": access_token,
            "refresh_token": "refresh-demo-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {
                "id": user_id,
                "name": data.name,
                "email": data.email,
                "roles": ["customer"],
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

        access_token = issue_token(str(user.id))

        return {
            "access_token": access_token,
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


def get_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    user_id = session_tokens.get(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    db = SessionLocal()

    try:
        user = db.execute(
            text("""
                SELECT id, role, active
                FROM users
                WHERE id = :id
            """),
            {"id": user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Token inválido")

        if not user.active:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        return AuthData(user_id=str(user.id), roles=[user.role])

    finally:
        db.close()


def require_admin(user: AuthData = Depends(get_user_from_token)):
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Solo administradores pueden acceder")

    return user


@app.post("/auth/logout", status_code=204)
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    session_tokens.pop(token, None)
    return


@app.post("/auth/validate")
def validate(user: AuthData = Depends(get_user_from_token)):
    return {
        "valid": True,
        "user": {
            "id": user.user_id,
            "roles": user.roles
        }
    }


@app.get("/auth/me")
def me(auth: AuthData = Depends(get_user_from_token)):
    db = SessionLocal()

    try:
        user = db.execute(
            text("""
                SELECT id, name, email, role, active
                FROM users
                WHERE id = :id
            """),
            {"id": auth.user_id}
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


@app.post("/auth/refresh")
def refresh_token(auth: AuthData = Depends(get_user_from_token)):
    new_token = issue_token(auth.user_id)

    return {
        "access_token": new_token,
        "refresh_token": "refresh-demo-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }


@app.get("/users")
def list_users(admin: AuthData = Depends(require_admin)):
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
def get_user(user_id: str, auth: AuthData = Depends(get_user_from_token)):
    if "admin" not in auth.roles and auth.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="No puedes ver datos de otro usuario"
        )

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
def update_user(
    user_id: str,
    data: UpdateProfileRequest,
    admin: AuthData = Depends(require_admin)
):
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

        return {"message": "Usuario actualizado correctamente"}

    finally:
        db.close()


@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    data: Optional[DeleteUserRequest] = None,
    auth: AuthData = Depends(get_user_from_token)
):
    db = SessionLocal()

    try:
        target = db.execute(
            text("SELECT id, password_hash FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not target:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if "admin" in auth.roles:
            db.execute(
                text("DELETE FROM users WHERE id = :id"),
                {"id": user_id}
            )
            db.commit()
            return

        if auth.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo el propietario puede eliminar su cuenta"
            )

        if not data or not data.current_password:
            raise HTTPException(
                status_code=401,
                detail="Contraseña requerida para eliminar la cuenta"
            )

        if not verify_password(data.current_password, target.password_hash):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        db.execute(
            text("DELETE FROM users WHERE id = :id"),
            {"id": user_id}
        )

        db.commit()
        return

    finally:
        db.close()


@app.patch("/users/{user_id}/password")
def change_password(
    user_id: str,
    data: ChangePasswordRequest,
    auth: AuthData = Depends(get_user_from_token)
):
    if auth.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes cambiar tu propia contraseña"
        )

    db = SessionLocal()

    try:
        user = db.execute(
            text("SELECT id, password_hash FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Contraseña actual incorrecta"
            )

        db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash
                WHERE id = :id
            """),
            {
                "password_hash": hash_password(data.new_password),
                "id": user_id
            }
        )

        db.commit()

        return {"message": "Contraseña actualizada correctamente"}

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

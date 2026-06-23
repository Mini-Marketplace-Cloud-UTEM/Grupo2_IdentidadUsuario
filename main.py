from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from uuid import uuid4

app = FastAPI(
    title="Mini Marketplace Cloud - Identidad, Usuarios y Sesiones",
    version="1.0.0",
    description="Mock API para E2"
)

# ==========================
# MODELOS
# ==========================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "customer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class AssignRoleRequest(BaseModel):
    role_name: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str]
    active: bool

# ==========================
# DATOS MOCK
# ==========================

mock_user = {
    "id": str(uuid4()),
    "name": "Matias González",
    "email": "matias@marketplace.com",
    "phone": "+56912345678",
    "avatar_url": "https://cdn.marketplace.local/avatar.jpg",
    "roles": ["customer"],
    "active": True
}

roles = [
    {
        "id": str(uuid4()),
        "name": "guest",
        "description": "Invitado",
        "permissions": []
    },
    {
        "id": str(uuid4()),
        "name": "customer",
        "description": "Cliente",
        "permissions": [
            "orders:read"
        ]
    },
    {
        "id": str(uuid4()),
        "name": "seller",
        "description": "Vendedor",
        "permissions": [
            "products:create",
            "products:edit"
        ]
    },
    {
        "id": str(uuid4()),
        "name": "admin",
        "description": "Administrador",
        "permissions": [
            "*"
        ]
    }
]

permissions = [
    {
        "name": "orders:read",
        "description": "Consultar pedidos"
    },
    {
        "name": "products:create",
        "description": "Crear productos"
    },
    {
        "name": "products:edit",
        "description": "Editar productos"
    }
]

# ==========================
# AUTH
# ==========================

@app.post("/auth/register", status_code=201)
def register(data: RegisterRequest):
    return {
        "access_token": "jwt-mock",
        "refresh_token": "refresh-mock",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            **mock_user,
            "name": data.name,
            "email": data.email
        }
    }

@app.post("/auth/login")
def login(data: LoginRequest):
    return {
        "access_token": "jwt-mock",
        "refresh_token": "refresh-mock",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": mock_user
    }

@app.post("/auth/logout", status_code=204)
def logout():
    return

@app.post("/auth/refresh")
def refresh(data: RefreshRequest):
    return {
        "access_token": "new-jwt-mock",
        "refresh_token": "new-refresh-mock",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": mock_user
    }

@app.post("/auth/validate")
def validate():
    return {
        "valid": True,
        "user": mock_user
    }

@app.get("/auth/me")
def me():
    return mock_user

# ==========================
# USERS
# ==========================

@app.get("/users")
def list_users():
    return {
        "total": 1,
        "page": 1,
        "limit": 20,
        "users": [mock_user]
    }

@app.get("/users/{user_id}")
def get_user(user_id: str):
    return mock_user

@app.put("/users/{user_id}")
def update_user(user_id: str, data: UpdateProfileRequest):

    updated = mock_user.copy()

    if data.name:
        updated["name"] = data.name

    if data.phone:
        updated["phone"] = data.phone

    if data.avatar_url:
        updated["avatar_url"] = data.avatar_url

    return updated

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    return

@app.patch("/users/{user_id}/password", status_code=204)
def change_password(user_id: str, data: ChangePasswordRequest):
    return

# ==========================
# IDENTITY
# ==========================

@app.get("/identity/roles")
def list_roles():
    return roles

@app.get("/identity/roles/{role_id}")
def get_role(role_id: str):

    for role in roles:
        if role["id"] == role_id:
            return role

    raise HTTPException(
        status_code=404,
        detail="Rol no encontrado"
    )

@app.get("/identity/permissions")
def list_permissions():
    return permissions

@app.get("/identity/users/{user_id}/roles")
def get_user_roles(user_id: str):
    return roles[:1]

@app.post("/identity/users/{user_id}/roles")
def assign_role(user_id: str, data: AssignRoleRequest):

    updated = mock_user.copy()

    if data.role_name not in updated["roles"]:
        updated["roles"].append(data.role_name)

    return updated

@app.delete(
    "/identity/users/{user_id}/roles/{role_id}",
    status_code=204
)
def remove_role(user_id: str, role_id: str):
    return

# ==========================
# ROOT
# ==========================

@app.get("/")
def root():
    return {
        "service": "Identity Service Mock",
        "status": "running"
    }
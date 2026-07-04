# Mini Marketplace Cloud - Grupo 2
# Servicio de Identidad, Usuarios y Sesiones

API REST desarrollada por el Grupo 2 para gestionar autenticación, usuarios, sesiones, roles y permisos del proyecto **Mini Marketplace Cloud**.

---

# Estado del proyecto

🟢 Funcional

El servicio cuenta con autenticación mediante **JWT**, documentación Swagger y despliegue en Render.

---

# URLs

**API desplegada**

https://grupo2-identidadusuario.onrender.com

**Swagger UI**

https://grupo2-identidadusuario.onrender.com/docs

---

# Tecnologías utilizadas

- Python 3
- FastAPI
- SQLAlchemy
- PostgreSQL (Supabase)
- JWT (python-jose)
- Swagger / OpenAPI
- Uvicorn
- Render

---

# Funcionalidades principales

- Registro de usuarios
- Inicio de sesión
- Cierre de sesión
- Validación de JWT
- Renovación de tokens (Refresh Token)
- Consulta del perfil autenticado
- Gestión de usuarios
- Cambio de contraseña
- Gestión de roles
- Control de permisos mediante JWT

---

# Endpoints principales

| Método | Endpoint | Descripción |
|---------|----------|-------------|
| POST | `/auth/register` | Registrar usuario |
| POST | `/auth/login` | Iniciar sesión |
| POST | `/auth/logout` | Cerrar sesión |
| POST | `/auth/validate` | Validar JWT |
| POST | `/auth/refresh` | Renovar Access Token |
| GET | `/auth/me` | Obtener usuario autenticado |
| GET | `/users` | Listar usuarios (Admin) |
| GET | `/users/{id}` | Obtener usuario |
| PUT | `/users/{id}` | Actualizar usuario (Admin) |
| DELETE | `/users/{id}` | Eliminar usuario |
| PATCH | `/users/{id}/password` | Cambiar contraseña |
| GET | `/identity/roles` | Listar roles |
| GET | `/identity/permissions` | Listar permisos |

---

# Autenticación

El servicio utiliza **JWT firmado con HS256**.

Luego de iniciar sesión se entrega:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Los endpoints protegidos requieren el siguiente header:

```http
Authorization: Bearer <access_token>
```

---

# Roles disponibles

| Rol | Descripción |
|------|-------------|
| guest | Usuario no autenticado |
| customer | Cliente del Marketplace |
| seller | Publicador de productos |
| admin | Administrador del sistema |

---

# Seguridad implementada

- Contraseñas almacenadas mediante SHA-256.
- Autenticación mediante JWT.
- Tokens con expiración.
- Refresh Token.
- Validación de sesión.
- Protección mediante Bearer Token.
- Registro público restringido al rol **customer**.
- Solo administradores pueden listar y modificar usuarios.
- Un usuario solo puede eliminar su propia cuenta.
- Los administradores pueden eliminar cualquier usuario.

---

# Códigos HTTP utilizados

| Código | Significado |
|---------|-------------|
| 200 | Operación exitosa |
| 201 | Recurso creado |
| 204 | Operación realizada sin contenido |
| 400 | Solicitud inválida |
| 401 | No autenticado |
| 403 | Acceso denegado |
| 404 | Recurso no encontrado |
| 409 | Conflicto (usuario ya existe) |
| 500 | Error interno |

---

# Modelo de autenticación

```
Cliente
      │
      │ Login
      ▼
Identity Service
      │
      │ JWT
      ▼
Cliente
      │
Authorization: Bearer <token>
      ▼
Endpoints protegidos
```

---

# Integración con otros servicios

Este servicio proporciona autenticación y autorización para:

- Frontend / BFF
- Carrito
- Pedidos
- Reportería
- Seguridad
- Auditoría

---

# Ejemplo de respuesta

### POST /auth/login

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "name": "Benjamín Barrientos",
    "email": "benjamin.barrientos@gmail.com",
    "roles": [
      "customer"
    ],
    "active": true
  }
}
```

---

# Ejecución local

Instalar dependencias

```bash
pip install -r requirements.txt
```

Ejecutar

```bash
uvicorn app.main:app --reload
```

Documentación disponible en:

```
http://localhost:8000/docs
```

---

# Equipo

**Grupo 2 – Identidad, Usuarios y Sesiones**

Proyecto Mini Marketplace Cloud

Universidad Tecnológica Metropolitana (UTEM)

2026

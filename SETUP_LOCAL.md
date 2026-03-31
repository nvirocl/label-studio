# Guía de desarrollo local — Label Studio (rama `copilot/add-user-roles-functionality`)

## Requisitos previos

- Docker y Docker Compose instalados
- Estar en la rama correcta: `copilot/add-user-roles-functionality`

---

## 1. Levantar la imagen Docker

### Primera vez (construir imagen desde el código fuente)

```bash
docker compose build
docker compose up -d
```

> ⏱️ El build puede tardar varios minutos la primera vez.

### Veces siguientes (sin cambios en el código)

```bash
docker compose up -d
```

### Verificar que los contenedores están corriendo

```bash
docker compose ps
```

Deberías ver 3 contenedores en estado `Up`:
- `label-studio-app-1` → backend Django (puerto interno 8000)
- `label-studio-nginx-1` → proxy nginx (puerto externo **8080**)
- `label-studio-db-1` → base de datos PostgreSQL

### Ver logs en tiempo real

```bash
docker compose logs -f app
```

---

## 2. Acceder a la interfaz web

Abre en el navegador: **http://localhost:8080**

La primera vez te pedirá registrar una cuenta (email + contraseña).

---

## 3. Obtener el token de API

### Opción A — Desde la interfaz web

1. Inicia sesión en http://localhost:8080
2. Ve a **Account & Settings** (ícono de usuario, arriba a la derecha)
3. En la sección **Access Token**, copia el token

### Opción B — Desde la terminal (recomendado para desarrollo)

```bash
docker compose exec app python /label-studio/label_studio/manage.py shell -c "
from users.models import User
u = User.objects.get(email='TU_EMAIL')
print(u.auth_token.key)
"
```

### Habilitar autenticación por token (solo la primera vez)

Por defecto, la autenticación por token legacy está deshabilitada. Hay que activarla:

```bash
docker compose exec app python /label-studio/label_studio/manage.py shell -c "
from users.models import User
u = User.objects.get(email='TU_EMAIL')
org = u.active_organization
org.jwt.legacy_api_tokens_enabled = True
org.jwt.save()
print('Token legacy habilitado correctamente')
"
```

---

## 4. Hacer llamadas a la API

Reemplaza `TU_TOKEN` con el token obtenido en el paso anterior.

### Verificar autenticación

```bash
curl -s -H "Authorization: Token TU_TOKEN" \
  http://localhost:8080/api/organizations/ | python3 -m json.tool
```

### Listar miembros de la organización (y sus roles)

```bash
curl -s -H "Authorization: Token TU_TOKEN" \
  http://localhost:8080/api/organizations/1/memberships | python3 -m json.tool
```

---

## 5. Probar la funcionalidad de roles (nueva en esta rama)

Esta rama agrega un campo `role` a cada miembro de la organización con los siguientes valores posibles:

| Rol        | Descripción                              |
|------------|------------------------------------------|
| `owner`    | Dueño de la organización (auto-asignado al crear) |
| `manager`  | Puede cambiar roles de otros miembros    |
| `reviewer` | Puede revisar anotaciones                |
| `annotator`| Solo puede anotar (rol por defecto)      |

### Cambiar el rol de un miembro

Primero obtén el `user_id` del miembro desde el listado de membresías:

```bash
curl -s -H "Authorization: Token TU_TOKEN" \
  http://localhost:8080/api/organizations/1/memberships | python3 -m json.tool
```

Luego cambia el rol (solo owners y managers pueden hacer esto):

```bash
curl -s -X PATCH \
  -H "Authorization: Token TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "reviewer"}' \
  http://localhost:8080/api/organizations/1/memberships/USER_ID/role | python3 -m json.tool
```

---

## 6. Documentación interactiva de la API (Swagger)

Con el servidor corriendo, accede a:

**http://localhost:8080/api/schema/swagger-ui/**

Busca la sección **Organizations** para ver todos los endpoints de roles.

---

## 7. Bajar los contenedores

```bash
# Bajar sin eliminar datos
docker compose down

# Bajar y eliminar volúmenes (borra la base de datos)
docker compose down -v
```

---

## Referencia rápida

| Acción | Comando |
|--------|---------|
| Levantar | `docker compose up -d` |
| Bajar | `docker compose down` |
| Ver logs | `docker compose logs -f app` |
| Rebuilding | `docker compose build && docker compose up -d` |
| URL app | http://localhost:8080 |
| URL Swagger | http://localhost:8080/api/schema/swagger-ui/ |

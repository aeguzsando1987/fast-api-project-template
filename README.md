# FastAPI Template - Plantilla Empresarial con Arquitectura de Capas

> Plantilla profesional FastAPI lista para proyectos empresariales con autenticación JWT, arquitectura de 7 capas y configuración híbrida.

## Características Principales

- **Arquitectura de 7 Capas** - Router → Controller → Service → Repository → Model → Database
- **Autenticación JWT** con OAuth2 integrado en Swagger
- **BaseRepository Genérico** con TypeVar[T] reutilizable en todas las entidades
- **Configuración Híbrida** - config.toml (público) + .env (secretos)
- **3 Entidades Base Completas**:
  - **Individual** - Ejemplo completo con 40+ campos, skills JSONB, validaciones
  - **Country** - Países con códigos ISO 3166 (3 países precargados)
  - **State** - Estados/Provincias/Departamentos (114 precargados)
- **Soft Delete** y campos de auditoría en todas las entidades
- **Inicialización Automática** de base de datos con datos geográficos
- **Sistema de Roles** de 5 niveles (Admin, Gerente, Colaborador, Lector, Guest)
- **Tests Unitarios** incluidos
- **Documentación Completa** con ejemplos paso a paso

---

## Requisitos Previos

- Python 3.8+
- PostgreSQL 12+
- Git

---

## Instalación Rápida

### 1. Clonar/Copiar Template

```bash
git clone <url-del-repositorio> mi-nuevo-proyecto
cd mi-nuevo-proyecto
```

### 2. Crear Ambiente Virtual

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos

```bash
# Crear base de datos en PostgreSQL
psql -U postgres
CREATE DATABASE mi_proyecto_db;
\q
```

### 5. Configurar Variables de Entorno

Editar `.env` con tu configuración (el template funciona sin .env con valores por defecto):

```env
# Base de datos
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/mi_proyecto_db

# JWT Security (generar con generate_secret_key.py)
SECRET_KEY=tu-clave-secreta-super-segura

# Admin por defecto
DEFAULT_ADMIN_EMAIL=admin@tuempresa.com
DEFAULT_ADMIN_PASSWORD=tu_password_seguro
```

### 6. Iniciar Aplicación

```bash
python main.py
```

### 7. Verificar Instalación

Abrir en el navegador:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

**Usuario Admin por Defecto:**
- Email: `admin@tuempresa.com`
- Password: `root`

---

## WebApp Demo Funcional

En la carpeta [webapp_demo/](../webapp_demo/) encontrarás aplicaciones web funcionales que consumen esta API:

### Vanilla JS Demo (95% Completo)
- Login con JWT y manejo de roles
- CRUD completo de Individuos con modales
- Dual View Mode (Dashboard cards y Tabla)
- Sistema de skills (backend listo)
- 10 bugs corregidos durante desarrollo
- Interfaz oscura con colores guindas (#8B1538)

Ver [webapp_demo/README.md](../webapp_demo/README.md) para instrucciones de uso.

---

## Documentación Completa

### Para Comenzar a Desarrollar

1. **[PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)** - **LECTURA OBLIGATORIA**
   - Ejemplo completo con entidades Técnico y Actividad
   - Patrón de 7 capas explicado paso a paso
   - POST común vs POST with user (para entidades de personal)
   - 8 ejemplos de Enums comunes
   - Código completo de las 6 capas por entidad
   - Pruebas en Swagger con ejemplos de requests/responses
   - Validaciones y transacciones atómicas

2. **[ADDING_ENTITIES.md](ADDING_ENTITIES.md)** - Guía paso a paso
   - Cómo agregar nuevas entidades al proyecto
   - Estructura de archivos necesarios
   - Ejemplos con Individual, Country, State
   - Checklist de implementación

### Arquitectura del Proyecto

```
app/
├── entities/              # Entidades del negocio
│   ├── individuals/       # Ejemplo completo (40+ campos)
│   ├── countries/        # Países con ISO codes
│   ├── states/           # Estados por país
│   └── users/            # Usuarios del sistema
│
├── shared/               # Código compartido
│   ├── base_repository.py        # Repository genérico
│   ├── exceptions.py              # Excepciones custom
│   ├── dependencies.py            # Dependencias FastAPI
│   ├── init_db.py                 # Auto-inicialización BD
│   └── data/                      # Datos precargados
│
└── tests/                # Tests unitarios
    ├── test_individuals/
    └── test_users/
```

---

## Agregar Nueva Entidad - Resumen Rápido

**Para agregar una nueva entidad (ej: Producto):**

1. Leer **[PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)** - Tiene el ejemplo completo
2. Crear carpeta `app/entities/productos/`
3. Crear 6 archivos siguiendo el patrón:
   - `models/producto.py` - Modelo SQLAlchemy
   - `schemas/producto_schemas.py` - Schemas Pydantic
   - `repositories/producto_repository.py` - Operaciones BD
   - `services/producto_service.py` - Lógica de negocio
   - `controllers/producto_controller.py` - Manejo de requests
   - `routers/producto_router.py` - Endpoints FastAPI
4. Registrar router en `main.py`
5. Probar en Swagger

**Consulta [PATRON_DESARROLLO.md](PATRON_DESARROLLO.md) para ver el código completo de cada archivo.**

---

## Endpoints Disponibles

### Autenticación
- `POST /token` - Obtener token JWT

### Usuarios
- `POST /users` - Crear usuario
- `GET /users` - Listar usuarios
- `GET /users/me` - Perfil actual
- `GET /users/roles` - Lista de roles disponibles
- `PUT /users/{id}` - Actualizar usuario
- `DELETE /users/{id}` - Eliminar usuario

### Individuals (Ejemplo completo)
- 25+ endpoints con CRUD, skills, búsquedas, cálculos

### Countries & States
- `GET /countries/` - Listar países (3 precargados)
- `GET /states/by-country/{id}` - Estados por país (114 precargados)

---

## Sistema de Permisos

### Jerarquía de Roles

| Rol | Nivel | Descripción | Permisos |
|-----|-------|-------------|----------|
| Admin | 1 | Administrador | Acceso total |
| Gerente | 2 | Manager | CRUD usuarios y entidades |
| Colaborador | 3 | Collaborator | CRUD entidades |
| Lector | 4 | Reader | Solo lectura |
| Guest | 5 | Invitado | Acceso limitado |

### Usar en Endpoints

```python
from app.shared.dependencies import get_current_user

# Solo Admin
@router.delete("/recurso/{id}")
def delete_recurso(current_user = Depends(get_current_user)):
    if current_user.role != 1:
        raise HTTPException(403, "Solo Admin")
```

Ver **[PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)** para ejemplos completos de autorización.

---

## Comandos Útiles

### Servidor
```bash
python main.py
```

### Ver Documentación
```
http://localhost:8001/docs
```

### Truncar Base de Datos
```bash
python truncate_db.py
```

### Ejecutar Tests
```bash
pytest app/tests/ -v
```

### Generar Secret Key
```bash
python generate_secret_key.py
```

---

## Configuración Híbrida

**config.toml** - Valores públicos (versionado en git):
- Configuración de features
- Límites de paginación
- Validaciones de negocio
- Pool de conexiones

**.env** - Valores secretos (NO versionar):
- DATABASE_URL
- SECRET_KEY
- Credenciales de admin

El sistema usa `.env` con fallback a `config.toml` para máxima flexibilidad.

---

## Estructura de Archivos

```
mi-proyecto/
├── app/
│   ├── entities/              # Entidades del negocio
│   ├── shared/                # Código compartido
│   └── tests/                 # Tests unitarios
├── main.py                    # Aplicación FastAPI
├── database.py               # Configuración DB
├── config.toml               # Config pública
├── .env                      # Config secreta
├── requirements.txt          # Dependencias
├── README.md                 # Este archivo
├── PATRON_DESARROLLO.md      # Guía de desarrollo
└── ADDING_ENTITIES.md        # Cómo agregar entidades
```

---

## Entidades Precargadas

Al iniciar el servidor por primera vez, se cargan automáticamente:

### Countries (3)
- United States (US/USA/840)
- Mexico (MX/MEX/484)
- Colombia (CO/COL/170)

### States (114)
- USA: 50 estados
- Mexico: 32 estados
- Colombia: 32 departamentos

---

## Próximos Pasos Después de Instalar

1. ✅ **Leer [PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)** - Entender el patrón completo
2. ✅ Explorar las 3 entidades base en `app/entities/`
3. ✅ Probar endpoints en Swagger (http://localhost:8001/docs)
4. ✅ Crear tu primera entidad siguiendo el patrón
5. ✅ Personalizar configuración en `config.toml` y `.env`

---

## Deployment a Producción

1. **Generar claves seguras:**
   ```bash
   python generate_secret_key.py
   ```

2. **Configurar .env** con valores de producción

3. **Usar servidor ASGI:**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

---

## Características Técnicas Avanzadas

- **BaseRepository Genérico** - Reutilizable con TypeVar[T]
- **Soft Delete** - No eliminación física de datos
- **Campos de Auditoría** - created_at, updated_at, updated_by
- **Validaciones en Múltiples Capas** - Pydantic + Lógica de Negocio
- **Transacciones Atómicas** - flush() + commit() para operaciones múltiples
- **Relaciones Bidireccionales** - SQLAlchemy relationships configuradas
- **Inicialización Idempotente** - No duplica datos en reinicios

---

## Soporte y Documentación

- **¿Cómo agregar una entidad?** → Ver [PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)
- **¿Cómo funciona la arquitectura?** → Ver [ADDING_ENTITIES.md](ADDING_ENTITIES.md)
- **¿Problemas con la instalación?** → Revisar logs en consola

---

## Autor

**Eric Guzman**

---

## Licencia

Template libre para uso en proyectos personales y comerciales.

---

**Última actualización:** 2025-10-03
**Versión:** 1.0.0
**Estado:** Producción Ready + WebApp Demo Funcional
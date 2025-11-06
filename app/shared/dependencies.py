"""
Dependencias compartidas para la aplicación

Este módulo contiene dependencias de FastAPI que se utilizan
en múltiples endpoints y capas de la aplicación.
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

# Importaciones que crearemos después
# from app.core.database import get_db
# from app.core.security import ALGORITHM, SECRET_KEY
# from app.entities.users.models.user import User

# Por ahora usamos las importaciones del archivo actual
from database import get_db, User
from auth import ALGORITHM, verify_token

import os
from dotenv import load_dotenv

load_dotenv()

# Configuración OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")


# ==================== DEPENDENCIAS DE AUTENTICACIÓN ====================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtiene el usuario actual a partir del token JWT.

    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe

    Ejemplo:
        @app.get("/profile")
        def get_profile(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id, "email": current_user.email}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decodificar token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscar usuario en base de datos
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Obtiene el usuario actual si está autenticado, None si no.

    Útil para endpoints que pueden funcionar con o sin autenticación.

    Args:
        token: Token JWT opcional
        db: Sesión de base de datos

    Returns:
        Usuario autenticado o None

    Ejemplo:
        @app.get("/public-endpoint")
        def public_endpoint(user: Optional[User] = Depends(get_optional_current_user)):
            if user:
                return {"message": f"Hola {user.name}!"}
            else:
                return {"message": "Hola invitado!"}
    """
    if not token:
        return None

    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


# ==================== DEPENDENCIAS DE AUTORIZACIÓN POR ROLES ====================

def require_role(minimum_role: int):
    """
    Crea una dependencia que requiere un rol mínimo específico.

    Args:
        minimum_role: Rol mínimo requerido (1=Admin, 2=Manager, etc.)

    Returns:
        Función de dependencia para FastAPI

    Ejemplo:
        # Solo admins (rol 1)
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: int,
            current_user: User = Depends(require_role(1))
        ):
            pass

        # Managers y admins (rol 2 o menor)
        @app.post("/reports")
        def create_report(
            current_user: User = Depends(require_role(2))
        ):
            pass
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role > minimum_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol de nivel {minimum_role} o superior"
            )
        return current_user

    return role_checker


# Dependencias predefinidas para roles comunes
require_admin = require_role(1)        # Solo administradores
require_manager = require_role(2)      # Managers y admins
require_employee = require_role(3)     # Empleados, managers y admins
require_any_user = require_role(5)     # Cualquier usuario autenticado


# ==================== DEPENDENCIAS DE PAGINACIÓN ====================

def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> dict:
    """
    Valida y retorna parámetros de paginación.

    Args:
        page: Número de página (mínimo 1)
        per_page: Registros por página
        max_per_page: Máximo registros permitidos por página

    Returns:
        Diccionario con parámetros validados

    Raises:
        HTTPException: Si los parámetros son inválidos

    Ejemplo:
        @app.get("/users")
        def list_users(
            pagination: dict = Depends(get_pagination_params),
            db: Session = Depends(get_db)
        ):
            return user_repository.paginate(
                page=pagination["page"],
                per_page=pagination["per_page"]
            )
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El número de página debe ser mayor a 0"
        )

    if per_page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los registros por página deben ser mayor a 0"
        )

    if per_page > max_per_page:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Máximo {max_per_page} registros por página permitidos"
        )

    return {
        "page": page,
        "per_page": per_page,
        "skip": (page - 1) * per_page
    }


# ==================== DEPENDENCIAS DE FILTROS ====================

def get_common_filters(
    active_only: bool = True,
    search: Optional[str] = None,
    order_by: Optional[str] = None,
    order_direction: str = "asc"
) -> dict:
    """
    Parámetros comunes de filtrado para endpoints de listado.

    Args:
        active_only: Si solo mostrar registros activos
        search: Término de búsqueda opcional
        order_by: Campo por el cual ordenar
        order_direction: Dirección del ordenamiento (asc/desc)

    Returns:
        Diccionario con filtros validados

    Ejemplo:
        @app.get("/persons")
        def list_persons(
            filters: dict = Depends(get_common_filters),
            pagination: dict = Depends(get_pagination_params),
            db: Session = Depends(get_db)
        ):
            return person_service.get_filtered_persons(filters, pagination)
    """
    if order_direction not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="order_direction debe ser 'asc' o 'desc'"
        )

    return {
        "active_only": active_only,
        "search": search.strip() if search else None,
        "order_by": order_by,
        "order_direction": order_direction
    }


# ==================== DEPENDENCIAS DE VALIDACIÓN DE IDS ====================

def validate_positive_int(value: int, field_name: str = "ID") -> int:
    """
    Valida que un entero sea positivo.

    Args:
        value: Valor a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        El valor validado

    Raises:
        HTTPException: Si el valor no es positivo
    """
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} debe ser un número positivo"
        )
    return value


def get_valid_id(id: int) -> int:
    """
    Dependencia para validar IDs en path parameters.

    Ejemplo:
        @app.get("/users/{user_id}")
        def get_user(
            user_id: int = Depends(get_valid_id),
            db: Session = Depends(get_db)
        ):
            return user_repository.get_by_id(user_id)
    """
    return validate_positive_int(id, "ID")


# ==================== DEPENDENCIAS DE CONFIGURACIÓN ====================

def get_app_settings():
    """
    Retorna configuración de la aplicación.

    Útil para acceder a configuración desde endpoints sin
    tener que importar directamente los módulos de config.

    Returns:
        Diccionario con configuración de la aplicación

    Ejemplo:
        @app.get("/health")
        def health_check(
            settings: dict = Depends(get_app_settings)
        ):
            return {
                "status": "ok",
                "version": settings["app_version"],
                "environment": settings["environment"]
            }
    """
    return {
        "app_name": os.getenv("APP_NAME", "Demo API"),
        "app_version": os.getenv("VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }


# ==================== DEPENDENCIAS DE PERMISOS GRANULARES ====================

def require_permission(entity: str, action: str, min_level: int = 1):
    """
    Crea una dependencia que valida permisos granulares por entidad y acción.

    Este sistema valida permisos específicos a nivel de endpoint, permitiendo
    control fino sobre qué operaciones puede realizar cada rol.

    Args:
        entity: Nombre de la entidad (ej: "individuals", "users")
        action: Acción específica (ej: "list", "create", "manage_skills")
        min_level: Nivel mínimo de permiso requerido (0-4)
            0 = None (sin acceso)
            1 = Read (solo lectura)
            2 = Update (lectura + actualización)
            3 = Create (lectura + creación + actualización)
            4 = Delete (acceso total)

    Returns:
        Función de dependencia para FastAPI que valida el permiso

    Ejemplo básico:
        @router.get("/individuals/")
        def list_individuals(
            current_user: User = Depends(require_permission("individuals", "list"))
        ):
            # Solo usuarios con permiso "individuals:list" pueden acceder
            pass

    Ejemplo con nivel mínimo:
        @router.delete("/individuals/{id}")
        def delete_individual(
            id: int,
            current_user: User = Depends(require_permission("individuals", "delete", min_level=4))
        ):
            # Solo usuarios con nivel 4 (Delete) o superior en "individuals:delete"
            pass

    Ejemplo con permiso custom:
        @router.post("/individuals/{id}/skills")
        def add_skill(
            id: int,
            skill_data: dict,
            current_user: User = Depends(require_permission("individuals", "manage_skills", min_level=3))
        ):
            # Permiso específico para gestión de skills
            pass

    Cómo funciona:
        1. Obtiene el usuario autenticado
        2. Busca el permiso específico en su rol (template)
        3. Valida el nivel mínimo requerido
        4. Permite o deniega el acceso

    NOTA: Para Fase 1, esta función verifica contra la tabla permission_templates.
    En fases posteriores, también verificará user_permissions (overrides individuales).
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        from app.shared.models.permission_template import PermissionTemplate
        from app.shared.models.permission_template_item import PermissionTemplateItem
        from app.shared.models.permission import Permission

        # 1. Obtener el template del rol del usuario
        # Mapeo de roles legacy (1-5) a nombres de templates
        role_mapping = {
            1: "Admin",
            2: "Manager",
            3: "Collaborator",
            4: "Reader",
            5: "Guest"
        }

        role_name = role_mapping.get(current_user.role)
        if not role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol de usuario inválido: {current_user.role}"
            )

        # 2. Buscar el template del rol
        template = db.query(PermissionTemplate).filter(
            PermissionTemplate.role_name == role_name,
            PermissionTemplate.is_active == True
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No se encontró configuración de permisos para el rol {role_name}"
            )

        # 3. Buscar el permiso específico entity:action
        permission = db.query(Permission).filter(
            Permission.entity == entity,
            Permission.action == action
        ).first()

        if not permission:
            # Permiso no definido en el sistema
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Permiso no configurado: {entity}:{action}"
            )

        # 4. Buscar el item de template que vincula el permiso con el rol
        template_item = db.query(PermissionTemplateItem).filter(
            PermissionTemplateItem.template_id == template.id,
            PermissionTemplateItem.permission_id == permission.id
        ).first()

        if not template_item:
            # El rol no tiene este permiso asignado
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu rol ({role_name}) no tiene permiso para: {entity}:{action}"
            )

        # 5. Validar el nivel del permiso
        if template_item.permission_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Nivel de permiso insuficiente. Requiere nivel {min_level}, tienes nivel {template_item.permission_level}"
            )

        # 6. TODO Fase 2: Verificar scope (all, own, team, department)
        # Por ahora todos los scopes son "all", esta validación se implementará después

        # 7. Permiso validado exitosamente
        return current_user

    return permission_checker
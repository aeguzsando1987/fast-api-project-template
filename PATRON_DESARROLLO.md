# Patron de Desarrollo - FastAPI Plantilla Empresarial

> Guia practica con ejemplo completo de dos entidades relacionadas

**Fecha creacion**: 2025-10-02
**Entidades ejemplo**: Tecnico y Actividad
**Proposito**: Demostrar el patron de desarrollo completo con relaciones N:1

---

## Arquitectura de 7 Capas

```
HTTP Request
    |
    v
[Router]           - Define rutas y endpoints
    |
    v
[Controller]       - Valida request, maneja response
    |
    v
[Service]          - Logica de negocio y validaciones
    |
    v
[Repository]       - Operaciones de base de datos
    |
    v
[Model]            - Definicion de tabla SQLAlchemy
    |
    v
[Database]         - PostgreSQL
```

---

## Estructura de Archivos

```
app/entities/
├── tecnicos/
│   ├── models/
│   │   └── tecnico.py
│   ├── schemas/
│   │   └── tecnico_schemas.py
│   ├── repositories/
│   │   └── tecnico_repository.py
│   ├── services/
│   │   └── tecnico_service.py
│   ├── controllers/
│   │   └── tecnico_controller.py
│   └── routers/
│       └── tecnico_router.py
│
└── actividades/
    ├── models/
    │   └── actividad.py
    ├── schemas/
    │   └── actividad_schemas.py
    ├── repositories/
    │   └── actividad_repository.py
    ├── services/
    │   └── actividad_service.py
    ├── controllers/
    │   └── actividad_controller.py
    └── routers/
        └── actividad_router.py
```

---

## Entidad 1: Tecnico (N:1 con User)

### 1.1 Model - tecnicos/models/tecnico.py

```python
"""
Modelo: Tecnico
Relacion: N:1 con User
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Tecnico(Base):
    """Modelo de tecnico que pertenece a un usuario."""

    __tablename__ = "tecnicos"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key - User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Campos de negocio
    codigo_tecnico = Column(String(20), unique=True, nullable=False, index=True)
    nombre_completo = Column(String(200), nullable=False)
    especialidad = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)

    # Campos de auditoria
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    user = relationship("User", back_populates="tecnicos")
    actividades = relationship("Actividad", back_populates="tecnico", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tecnico(id={self.id}, codigo={self.codigo_tecnico}, nombre={self.nombre_completo})>"
```

### 1.2 Schema - tecnicos/schemas/tecnico_schemas.py

```python
"""
Schemas: Tecnico
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class TecnicoBase(BaseModel):
    """Schema base para Tecnico."""
    codigo_tecnico: str = Field(..., min_length=3, max_length=20, description="Codigo unico del tecnico")
    nombre_completo: str = Field(..., min_length=3, max_length=200, description="Nombre completo")
    especialidad: str = Field(..., min_length=3, max_length=100, description="Especialidad del tecnico")
    telefono: Optional[str] = Field(None, max_length=20, description="Telefono de contacto")
    email: Optional[EmailStr] = Field(None, description="Email de contacto")


class TecnicoCreate(TecnicoBase):
    """Schema para crear un tecnico (POST comun - requiere user_id existente)."""
    user_id: int = Field(..., gt=0, description="ID del usuario asociado")


class TecnicoCreateWithUser(TecnicoBase):
    """Schema para crear un tecnico junto con su usuario (POST with user)."""
    user_email: str = Field(..., description="Email del usuario a crear")
    user_password: str = Field(..., min_length=8, description="Password del usuario")
    user_username: Optional[str] = Field(None, description="Username (opcional, usa email por defecto)")


class TecnicoUpdate(BaseModel):
    """Schema para actualizar un tecnico."""
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    especialidad: Optional[str] = Field(None, min_length=3, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class TecnicoResponse(TecnicoBase):
    """Schema de respuesta para Tecnico."""
    id: int
    user_id: int
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TecnicoListResponse(BaseModel):
    """Schema para lista de tecnicos."""
    total: int
    items: list[TecnicoResponse]
```

### 1.3 Repository - tecnicos/repositories/tecnico_repository.py

```python
"""
Repositorio: Tecnico
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.shared.base_repository import BaseRepository
from app.entities.tecnicos.models.tecnico import Tecnico


class TecnicoRepository(BaseRepository[Tecnico]):
    """Repositorio para operaciones de datos de Tecnico."""

    def __init__(self, db: Session):
        super().__init__(Tecnico, db)

    def get_by_codigo(self, codigo_tecnico: str) -> Optional[Tecnico]:
        """Obtiene un tecnico por su codigo."""
        return self.db.query(Tecnico).filter(
            Tecnico.codigo_tecnico == codigo_tecnico.upper(),
            Tecnico.is_deleted == False
        ).first()

    def get_by_user(self, user_id: int) -> List[Tecnico]:
        """Obtiene todos los tecnicos de un usuario."""
        return self.db.query(Tecnico).filter(
            Tecnico.user_id == user_id,
            Tecnico.is_deleted == False
        ).all()

    def get_by_especialidad(self, especialidad: str) -> List[Tecnico]:
        """Obtiene tecnicos por especialidad."""
        return self.db.query(Tecnico).filter(
            Tecnico.especialidad.ilike(f"%{especialidad}%"),
            Tecnico.is_deleted == False
        ).all()

    def get_active_only(self, skip: int = 0, limit: int = 100) -> List[Tecnico]:
        """Obtiene solo tecnicos activos."""
        return self.db.query(Tecnico).filter(
            Tecnico.is_active == True,
            Tecnico.is_deleted == False
        ).offset(skip).limit(limit).all()
```

### 1.4 Service - tecnicos/services/tecnico_service.py

```python
"""
Servicio: Tecnico
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.entities.tecnicos.repositories.tecnico_repository import TecnicoRepository
from app.entities.tecnicos.schemas.tecnico_schemas import TecnicoCreate, TecnicoUpdate
from app.entities.tecnicos.models.tecnico import Tecnico
from app.shared.exceptions import EntityNotFoundError, EntityAlreadyExistsError, EntityValidationError


class TecnicoService:
    """Servicio para logica de negocio de Tecnico."""

    def __init__(self, db: Session):
        self.repository = TecnicoRepository(db)
        self.db = db

    def create_tecnico(self, tecnico_data: TecnicoCreate) -> Tecnico:
        """Crea un nuevo tecnico (POST comun - requiere user_id existente)."""
        # Validar que el codigo no exista
        existing = self.repository.get_by_codigo(tecnico_data.codigo_tecnico)
        if existing:
            raise EntityAlreadyExistsError("Tecnico", "codigo_tecnico", tecnico_data.codigo_tecnico)

        # Validar que el usuario exista (opcional - depende de tu logica)
        # user = self.db.query(User).filter(User.id == tecnico_data.user_id).first()
        # if not user:
        #     raise EntityNotFoundError("User", tecnico_data.user_id)

        # Crear tecnico
        tecnico = Tecnico(
            user_id=tecnico_data.user_id,
            codigo_tecnico=tecnico_data.codigo_tecnico.upper(),
            nombre_completo=tecnico_data.nombre_completo,
            especialidad=tecnico_data.especialidad,
            telefono=tecnico_data.telefono,
            email=tecnico_data.email
        )

        return self.repository.create(tecnico)

    def create_tecnico_with_user(self, tecnico_data: TecnicoCreate, user_data: dict) -> Tecnico:
        """Crea un tecnico junto con su usuario (POST with user)."""
        from app.entities.users.models.user import User
        from app.shared.security import get_password_hash

        # Validar que el codigo no exista
        existing = self.repository.get_by_codigo(tecnico_data.codigo_tecnico)
        if existing:
            raise EntityAlreadyExistsError("Tecnico", "codigo_tecnico", tecnico_data.codigo_tecnico)

        # Validar que el email del usuario no exista
        existing_user = self.db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            raise EntityAlreadyExistsError("User", "email", user_data["email"])

        # Crear usuario primero
        new_user = User(
            email=user_data["email"],
            username=user_data.get("username", user_data["email"]),
            hashed_password=get_password_hash(user_data["password"]),
            is_active=True
        )
        self.db.add(new_user)
        self.db.flush()  # Para obtener el ID del usuario sin hacer commit

        # Crear tecnico asociado al usuario
        tecnico = Tecnico(
            user_id=new_user.id,
            codigo_tecnico=tecnico_data.codigo_tecnico.upper(),
            nombre_completo=tecnico_data.nombre_completo,
            especialidad=tecnico_data.especialidad,
            telefono=tecnico_data.telefono,
            email=tecnico_data.email
        )

        created_tecnico = self.repository.create(tecnico)
        self.db.commit()  # Commit de ambas transacciones
        return created_tecnico

    def get_tecnico(self, tecnico_id: int) -> Tecnico:
        """Obtiene un tecnico por ID."""
        tecnico = self.repository.get_by_id(tecnico_id)
        if not tecnico:
            raise EntityNotFoundError("Tecnico", tecnico_id)
        return tecnico

    def get_all_tecnicos(self, skip: int = 0, limit: int = 100) -> List[Tecnico]:
        """Obtiene todos los tecnicos."""
        return self.repository.get_all(skip=skip, limit=limit)

    def update_tecnico(self, tecnico_id: int, tecnico_data: TecnicoUpdate) -> Tecnico:
        """Actualiza un tecnico."""
        tecnico = self.get_tecnico(tecnico_id)

        update_data = tecnico_data.model_dump(exclude_unset=True)
        return self.repository.update(tecnico, update_data)

    def delete_tecnico(self, tecnico_id: int) -> bool:
        """Elimina un tecnico (soft delete)."""
        tecnico = self.get_tecnico(tecnico_id)
        return self.repository.delete(tecnico)

    def get_by_user(self, user_id: int) -> List[Tecnico]:
        """Obtiene tecnicos por usuario."""
        return self.repository.get_by_user(user_id)

    def get_by_especialidad(self, especialidad: str) -> List[Tecnico]:
        """Obtiene tecnicos por especialidad."""
        return self.repository.get_by_especialidad(especialidad)
```

### 1.5 Controller - tecnicos/controllers/tecnico_controller.py

```python
"""
Controlador: Tecnico
"""
from typing import List
from sqlalchemy.orm import Session

from app.entities.tecnicos.services.tecnico_service import TecnicoService
from app.entities.tecnicos.schemas.tecnico_schemas import (
    TecnicoCreate, TecnicoCreateWithUser, TecnicoUpdate, TecnicoResponse, TecnicoListResponse
)


class TecnicoController:
    """Controlador para manejar requests de Tecnico."""

    def __init__(self, db: Session):
        self.service = TecnicoService(db)

    def create(self, tecnico_data: TecnicoCreate) -> TecnicoResponse:
        """Crea un nuevo tecnico (POST comun - requiere user_id existente)."""
        tecnico = self.service.create_tecnico(tecnico_data)
        return TecnicoResponse.model_validate(tecnico)

    def create_with_user(self, tecnico_data: TecnicoCreateWithUser) -> TecnicoResponse:
        """Crea un tecnico junto con su usuario (POST with user)."""
        user_data = {
            "email": tecnico_data.user_email,
            "password": tecnico_data.user_password,
            "username": tecnico_data.user_username
        }
        # Crear TecnicoCreate sin el user_id (se genera en el service)
        tecnico_create = TecnicoCreate(
            user_id=0,  # Temporal, se reemplaza en el service
            codigo_tecnico=tecnico_data.codigo_tecnico,
            nombre_completo=tecnico_data.nombre_completo,
            especialidad=tecnico_data.especialidad,
            telefono=tecnico_data.telefono,
            email=tecnico_data.email
        )
        tecnico = self.service.create_tecnico_with_user(tecnico_create, user_data)
        return TecnicoResponse.model_validate(tecnico)

    def get_by_id(self, tecnico_id: int) -> TecnicoResponse:
        """Obtiene un tecnico por ID."""
        tecnico = self.service.get_tecnico(tecnico_id)
        return TecnicoResponse.model_validate(tecnico)

    def get_all(self, skip: int = 0, limit: int = 100) -> TecnicoListResponse:
        """Obtiene todos los tecnicos."""
        tecnicos = self.service.get_all_tecnicos(skip=skip, limit=limit)
        return TecnicoListResponse(
            total=len(tecnicos),
            items=[TecnicoResponse.model_validate(t) for t in tecnicos]
        )

    def update(self, tecnico_id: int, tecnico_data: TecnicoUpdate) -> TecnicoResponse:
        """Actualiza un tecnico."""
        tecnico = self.service.update_tecnico(tecnico_id, tecnico_data)
        return TecnicoResponse.model_validate(tecnico)

    def delete(self, tecnico_id: int) -> dict:
        """Elimina un tecnico."""
        self.service.delete_tecnico(tecnico_id)
        return {"message": "Tecnico eliminado exitosamente"}

    def get_by_user(self, user_id: int) -> List[TecnicoResponse]:
        """Obtiene tecnicos por usuario."""
        tecnicos = self.service.get_by_user(user_id)
        return [TecnicoResponse.model_validate(t) for t in tecnicos]

    def get_by_especialidad(self, especialidad: str) -> List[TecnicoResponse]:
        """Obtiene tecnicos por especialidad."""
        tecnicos = self.service.get_by_especialidad(especialidad)
        return [TecnicoResponse.model_validate(t) for t in tecnicos]
```

### 1.6 Router - tecnicos/routers/tecnico_router.py

```python
"""
Router: Tecnico
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.entities.tecnicos.controllers.tecnico_controller import TecnicoController
from app.entities.tecnicos.schemas.tecnico_schemas import (
    TecnicoCreate, TecnicoCreateWithUser, TecnicoUpdate, TecnicoResponse, TecnicoListResponse
)
from app.shared.dependencies import get_db, get_current_user

router = APIRouter(prefix="/tecnicos", tags=["Tecnicos"])


@router.post("/", response_model=TecnicoResponse, status_code=status.HTTP_201_CREATED)
def create_tecnico(
    tecnico_data: TecnicoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Crea un nuevo tecnico (POST comun - requiere user_id existente)."""
    controller = TecnicoController(db)
    return controller.create(tecnico_data)


@router.post("/with-user", response_model=TecnicoResponse, status_code=status.HTTP_201_CREATED)
def create_tecnico_with_user(
    tecnico_data: TecnicoCreateWithUser,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Crea un tecnico junto con su usuario (POST with user)."""
    controller = TecnicoController(db)
    return controller.create_with_user(tecnico_data)


@router.get("/", response_model=TecnicoListResponse)
def get_all_tecnicos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene todos los tecnicos."""
    controller = TecnicoController(db)
    return controller.get_all(skip=skip, limit=limit)


@router.get("/{tecnico_id}", response_model=TecnicoResponse)
def get_tecnico(
    tecnico_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un tecnico por ID."""
    controller = TecnicoController(db)
    return controller.get_by_id(tecnico_id)


@router.put("/{tecnico_id}", response_model=TecnicoResponse)
def update_tecnico(
    tecnico_id: int,
    tecnico_data: TecnicoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Actualiza un tecnico."""
    controller = TecnicoController(db)
    return controller.update(tecnico_id, tecnico_data)


@router.delete("/{tecnico_id}", status_code=status.HTTP_200_OK)
def delete_tecnico(
    tecnico_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Elimina un tecnico (soft delete)."""
    controller = TecnicoController(db)
    return controller.delete(tecnico_id)


@router.get("/user/{user_id}", response_model=list[TecnicoResponse])
def get_tecnicos_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene todos los tecnicos de un usuario."""
    controller = TecnicoController(db)
    return controller.get_by_user(user_id)


@router.get("/especialidad/{especialidad}", response_model=list[TecnicoResponse])
def get_tecnicos_by_especialidad(
    especialidad: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene tecnicos por especialidad."""
    controller = TecnicoController(db)
    return controller.get_by_especialidad(especialidad)
```

---

## Entidad 2: Actividad (N:1 con Tecnico)

### 2.1 Model - actividades/models/actividad.py

```python
"""
Modelo: Actividad
Relacion: N:1 con Tecnico
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ActividadEstado(str, enum.Enum):
    """Estados posibles de una actividad."""
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"


class Actividad(Base):
    """Modelo de actividad realizada por un tecnico."""

    __tablename__ = "actividades"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key - Tecnico
    tecnico_id = Column(Integer, ForeignKey("tecnicos.id"), nullable=False)

    # Campos de negocio
    codigo_actividad = Column(String(30), unique=True, nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    estado = Column(SQLEnum(ActividadEstado), default=ActividadEstado.PENDIENTE, nullable=False)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    ubicacion = Column(String(300), nullable=True)

    # Campos de auditoria
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    tecnico = relationship("Tecnico", back_populates="actividades")

    def __repr__(self):
        return f"<Actividad(id={self.id}, codigo={self.codigo_actividad}, titulo={self.titulo})>"
```

### 2.2 Schema - actividades/schemas/actividad_schemas.py

```python
"""
Schemas: Actividad
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class ActividadEstadoEnum(str, Enum):
    """Estados de actividad."""
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"


class ActividadBase(BaseModel):
    """Schema base para Actividad."""
    codigo_actividad: str = Field(..., min_length=3, max_length=30, description="Codigo unico de actividad")
    titulo: str = Field(..., min_length=3, max_length=200, description="Titulo de la actividad")
    descripcion: Optional[str] = Field(None, description="Descripcion detallada")
    estado: ActividadEstadoEnum = Field(default=ActividadEstadoEnum.PENDIENTE, description="Estado actual")
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha de inicio")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha de finalizacion")
    ubicacion: Optional[str] = Field(None, max_length=300, description="Ubicacion de la actividad")


class ActividadCreate(ActividadBase):
    """Schema para crear una actividad."""
    tecnico_id: int = Field(..., gt=0, description="ID del tecnico asignado")


class ActividadUpdate(BaseModel):
    """Schema para actualizar una actividad."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = None
    estado: Optional[ActividadEstadoEnum] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    ubicacion: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class ActividadResponse(ActividadBase):
    """Schema de respuesta para Actividad."""
    id: int
    tecnico_id: int
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActividadListResponse(BaseModel):
    """Schema para lista de actividades."""
    total: int
    items: list[ActividadResponse]
```

### 2.3 Repository - actividades/repositories/actividad_repository.py

```python
"""
Repositorio: Actividad
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.shared.base_repository import BaseRepository
from app.entities.actividades.models.actividad import Actividad, ActividadEstado


class ActividadRepository(BaseRepository[Actividad]):
    """Repositorio para operaciones de datos de Actividad."""

    def __init__(self, db: Session):
        super().__init__(Actividad, db)

    def get_by_codigo(self, codigo_actividad: str) -> Optional[Actividad]:
        """Obtiene una actividad por su codigo."""
        return self.db.query(Actividad).filter(
            Actividad.codigo_actividad == codigo_actividad.upper(),
            Actividad.is_deleted == False
        ).first()

    def get_by_tecnico(self, tecnico_id: int) -> List[Actividad]:
        """Obtiene todas las actividades de un tecnico."""
        return self.db.query(Actividad).filter(
            Actividad.tecnico_id == tecnico_id,
            Actividad.is_deleted == False
        ).all()

    def get_by_estado(self, estado: ActividadEstado) -> List[Actividad]:
        """Obtiene actividades por estado."""
        return self.db.query(Actividad).filter(
            Actividad.estado == estado,
            Actividad.is_deleted == False
        ).all()

    def get_active_only(self, skip: int = 0, limit: int = 100) -> List[Actividad]:
        """Obtiene solo actividades activas."""
        return self.db.query(Actividad).filter(
            Actividad.is_active == True,
            Actividad.is_deleted == False
        ).offset(skip).limit(limit).all()

    def search_by_titulo(self, titulo: str) -> List[Actividad]:
        """Busca actividades por titulo."""
        return self.db.query(Actividad).filter(
            Actividad.titulo.ilike(f"%{titulo}%"),
            Actividad.is_deleted == False
        ).all()
```

### 2.4 Service - actividades/services/actividad_service.py

```python
"""
Servicio: Actividad
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.entities.actividades.repositories.actividad_repository import ActividadRepository
from app.entities.actividades.schemas.actividad_schemas import ActividadCreate, ActividadUpdate
from app.entities.actividades.models.actividad import Actividad, ActividadEstado
from app.shared.exceptions import EntityNotFoundError, EntityAlreadyExistsError, EntityValidationError


class ActividadService:
    """Servicio para logica de negocio de Actividad."""

    def __init__(self, db: Session):
        self.repository = ActividadRepository(db)
        self.db = db

    def create_actividad(self, actividad_data: ActividadCreate) -> Actividad:
        """Crea una nueva actividad."""
        # Validar que el codigo no exista
        existing = self.repository.get_by_codigo(actividad_data.codigo_actividad)
        if existing:
            raise EntityAlreadyExistsError("Actividad", "codigo_actividad", actividad_data.codigo_actividad)

        # Validar que el tecnico exista (opcional)
        # tecnico = self.db.query(Tecnico).filter(Tecnico.id == actividad_data.tecnico_id).first()
        # if not tecnico:
        #     raise EntityNotFoundError("Tecnico", actividad_data.tecnico_id)

        # Validar fechas
        if actividad_data.fecha_inicio and actividad_data.fecha_fin:
            if actividad_data.fecha_inicio > actividad_data.fecha_fin:
                raise EntityValidationError("Actividad", {
                    "fecha_inicio": "La fecha de inicio no puede ser posterior a la fecha de fin"
                })

        # Crear actividad
        actividad = Actividad(
            tecnico_id=actividad_data.tecnico_id,
            codigo_actividad=actividad_data.codigo_actividad.upper(),
            titulo=actividad_data.titulo,
            descripcion=actividad_data.descripcion,
            estado=actividad_data.estado,
            fecha_inicio=actividad_data.fecha_inicio,
            fecha_fin=actividad_data.fecha_fin,
            ubicacion=actividad_data.ubicacion
        )

        return self.repository.create(actividad)

    def get_actividad(self, actividad_id: int) -> Actividad:
        """Obtiene una actividad por ID."""
        actividad = self.repository.get_by_id(actividad_id)
        if not actividad:
            raise EntityNotFoundError("Actividad", actividad_id)
        return actividad

    def get_all_actividades(self, skip: int = 0, limit: int = 100) -> List[Actividad]:
        """Obtiene todas las actividades."""
        return self.repository.get_all(skip=skip, limit=limit)

    def update_actividad(self, actividad_id: int, actividad_data: ActividadUpdate) -> Actividad:
        """Actualiza una actividad."""
        actividad = self.get_actividad(actividad_id)

        # Validar fechas si se proporcionan
        update_data = actividad_data.model_dump(exclude_unset=True)
        if "fecha_inicio" in update_data and "fecha_fin" in update_data:
            if update_data["fecha_inicio"] > update_data["fecha_fin"]:
                raise EntityValidationError("Actividad", {
                    "fecha_inicio": "La fecha de inicio no puede ser posterior a la fecha de fin"
                })

        return self.repository.update(actividad, update_data)

    def delete_actividad(self, actividad_id: int) -> bool:
        """Elimina una actividad (soft delete)."""
        actividad = self.get_actividad(actividad_id)
        return self.repository.delete(actividad)

    def get_by_tecnico(self, tecnico_id: int) -> List[Actividad]:
        """Obtiene actividades por tecnico."""
        return self.repository.get_by_tecnico(tecnico_id)

    def get_by_estado(self, estado: str) -> List[Actividad]:
        """Obtiene actividades por estado."""
        estado_enum = ActividadEstado(estado.upper())
        return self.repository.get_by_estado(estado_enum)
```

### 2.5 Controller - actividades/controllers/actividad_controller.py

```python
"""
Controlador: Actividad
"""
from typing import List
from sqlalchemy.orm import Session

from app.entities.actividades.services.actividad_service import ActividadService
from app.entities.actividades.schemas.actividad_schemas import (
    ActividadCreate, ActividadUpdate, ActividadResponse, ActividadListResponse
)


class ActividadController:
    """Controlador para manejar requests de Actividad."""

    def __init__(self, db: Session):
        self.service = ActividadService(db)

    def create(self, actividad_data: ActividadCreate) -> ActividadResponse:
        """Crea una nueva actividad."""
        actividad = self.service.create_actividad(actividad_data)
        return ActividadResponse.model_validate(actividad)

    def get_by_id(self, actividad_id: int) -> ActividadResponse:
        """Obtiene una actividad por ID."""
        actividad = self.service.get_actividad(actividad_id)
        return ActividadResponse.model_validate(actividad)

    def get_all(self, skip: int = 0, limit: int = 100) -> ActividadListResponse:
        """Obtiene todas las actividades."""
        actividades = self.service.get_all_actividades(skip=skip, limit=limit)
        return ActividadListResponse(
            total=len(actividades),
            items=[ActividadResponse.model_validate(a) for a in actividades]
        )

    def update(self, actividad_id: int, actividad_data: ActividadUpdate) -> ActividadResponse:
        """Actualiza una actividad."""
        actividad = self.service.update_actividad(actividad_id, actividad_data)
        return ActividadResponse.model_validate(actividad)

    def delete(self, actividad_id: int) -> dict:
        """Elimina una actividad."""
        self.service.delete_actividad(actividad_id)
        return {"message": "Actividad eliminada exitosamente"}

    def get_by_tecnico(self, tecnico_id: int) -> List[ActividadResponse]:
        """Obtiene actividades por tecnico."""
        actividades = self.service.get_by_tecnico(tecnico_id)
        return [ActividadResponse.model_validate(a) for a in actividades]

    def get_by_estado(self, estado: str) -> List[ActividadResponse]:
        """Obtiene actividades por estado."""
        actividades = self.service.get_by_estado(estado)
        return [ActividadResponse.model_validate(a) for a in actividades]
```

### 2.6 Router - actividades/routers/actividad_router.py

```python
"""
Router: Actividad
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.entities.actividades.controllers.actividad_controller import ActividadController
from app.entities.actividades.schemas.actividad_schemas import (
    ActividadCreate, ActividadUpdate, ActividadResponse, ActividadListResponse
)
from app.shared.dependencies import get_db, get_current_user

router = APIRouter(prefix="/actividades", tags=["Actividades"])


@router.post("/", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
def create_actividad(
    actividad_data: ActividadCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Crea una nueva actividad."""
    controller = ActividadController(db)
    return controller.create(actividad_data)


@router.get("/", response_model=ActividadListResponse)
def get_all_actividades(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene todas las actividades."""
    controller = ActividadController(db)
    return controller.get_all(skip=skip, limit=limit)


@router.get("/{actividad_id}", response_model=ActividadResponse)
def get_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una actividad por ID."""
    controller = ActividadController(db)
    return controller.get_by_id(actividad_id)


@router.put("/{actividad_id}", response_model=ActividadResponse)
def update_actividad(
    actividad_id: int,
    actividad_data: ActividadUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Actualiza una actividad."""
    controller = ActividadController(db)
    return controller.update(actividad_id, actividad_data)


@router.delete("/{actividad_id}", status_code=status.HTTP_200_OK)
def delete_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Elimina una actividad (soft delete)."""
    controller = ActividadController(db)
    return controller.delete(actividad_id)


@router.get("/tecnico/{tecnico_id}", response_model=list[ActividadResponse])
def get_actividades_by_tecnico(
    tecnico_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene todas las actividades de un tecnico."""
    controller = ActividadController(db)
    return controller.get_by_tecnico(tecnico_id)


@router.get("/estado/{estado}", response_model=list[ActividadResponse])
def get_actividades_by_estado(
    estado: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene actividades por estado."""
    controller = ActividadController(db)
    return controller.get_by_estado(estado)
```

---

## Paso 3: Registrar en main.py

```python
# Importar routers
from app.entities.tecnicos.routers.tecnico_router import router as tecnico_router
from app.entities.actividades.routers.actividad_router import router as actividad_router

# Registrar routers en la aplicacion
app.include_router(tecnico_router)
app.include_router(actividad_router)
```

---

## Paso 4: Crear tablas en base de datos

**Metodo 1: Automatico (recomendado para desarrollo)**

Las tablas se crearan automaticamente al iniciar el servidor si tienes configurado:

```python
# En main.py o database.py
from app.database import Base, engine

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
```

**Metodo 2: Manual con script**

```bash
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

**Metodo 3: Alembic (recomendado para produccion)**

```bash
alembic revision --autogenerate -m "Add Tecnico and Actividad tables"
alembic upgrade head
```

---

## Paso 5: Probar en Swagger

1. **Iniciar servidor**:
   ```bash
   python main.py
   ```

2. **Abrir Swagger UI**:
   ```
   http://localhost:8001/docs
   ```

3. **Obtener token de autenticacion**:
   - POST /token
   - username: admin@tuempresa.com
   - password: root

4. **Autorizar en Swagger**:
   - Click en "Authorize"
   - Pegar el token
   - Click "Authorize"

5. **Probar endpoints de Tecnico** (IMPORTANTE: Dos formas de crear):

   **Opcion 1: POST comun - Crear Tecnico (con user_id existente)**:
   ```json
   POST /tecnicos/
   {
     "user_id": 1,
     "codigo_tecnico": "TEC001",
     "nombre_completo": "Juan Perez",
     "especialidad": "Electricidad",
     "telefono": "+57 300 123 4567",
     "email": "juan.perez@empresa.com"
   }
   ```

   **Opcion 2: POST with user - Crear Tecnico + Usuario (crea ambos)**:
   ```json
   POST /tecnicos/with-user
   {
     "codigo_tecnico": "TEC002",
     "nombre_completo": "Maria Rodriguez",
     "especialidad": "Plomeria",
     "telefono": "+57 300 999 8888",
     "email": "maria.rodriguez@empresa.com",
     "user_email": "maria.rod@sistema.com",
     "user_password": "SecurePass123!",
     "user_username": "maria.rod"
   }
   ```

   **Response de POST with user**:
   ```json
   {
     "id": 2,
     "user_id": 5,
     "codigo_tecnico": "TEC002",
     "nombre_completo": "Maria Rodriguez",
     "especialidad": "Plomeria",
     "telefono": "+57 300 999 8888",
     "email": "maria.rodriguez@empresa.com",
     "is_active": true,
     "is_deleted": false,
     "created_at": "2025-10-02T15:30:00",
     "updated_at": "2025-10-02T15:30:00"
   }
   ```

   **Nota**: Observa que se creo el tecnico con ID 2 y automaticamente se creo un usuario con ID 5.

   **Listar Tecnicos**:
   ```
   GET /tecnicos/
   ```

   **Obtener Tecnico por ID**:
   ```
   GET /tecnicos/1
   ```

   **Actualizar Tecnico**:
   ```json
   PUT /tecnicos/1
   {
     "especialidad": "Electricidad Industrial",
     "telefono": "+57 300 999 8888"
   }
   ```

   **Tecnicos por Usuario**:
   ```
   GET /tecnicos/user/1
   ```

6. **Probar endpoints de Actividad** (NOTA: Aqui se usan los ENUMS):

   **Crear Actividad con ENUM estado**:
   ```json
   POST /actividades/
   {
     "tecnico_id": 1,
     "codigo_actividad": "ACT001",
     "titulo": "Instalacion de panel electrico",
     "descripcion": "Instalacion de panel electrico en edificio norte",
     "estado": "PENDIENTE",
     "fecha_inicio": "2025-10-03T08:00:00",
     "ubicacion": "Edificio Norte - Piso 3"
   }
   ```

   **Response con ENUM**:
   ```json
   {
     "id": 1,
     "tecnico_id": 1,
     "codigo_actividad": "ACT001",
     "titulo": "Instalacion de panel electrico",
     "descripcion": "Instalacion de panel electrico en edificio norte",
     "estado": "PENDIENTE",
     "fecha_inicio": "2025-10-03T08:00:00",
     "fecha_fin": null,
     "ubicacion": "Edificio Norte - Piso 3",
     "is_active": true,
     "is_deleted": false,
     "created_at": "2025-10-02T10:30:00",
     "updated_at": "2025-10-02T10:30:00"
   }
   ```

   **Listar Actividades**:
   ```
   GET /actividades/
   ```

   **Actividades por Tecnico**:
   ```
   GET /actividades/tecnico/1
   ```

   **Actividades por Estado (usando valores del ENUM)**:
   ```
   GET /actividades/estado/PENDIENTE
   GET /actividades/estado/EN_PROCESO
   GET /actividades/estado/COMPLETADA
   GET /actividades/estado/CANCELADA
   ```

   **Actualizar Estado (cambiando valor del ENUM)**:
   ```json
   PUT /actividades/1
   {
     "estado": "EN_PROCESO",
     "fecha_inicio": "2025-10-03T09:00:00"
   }
   ```

   **Cambiar a COMPLETADA**:
   ```json
   PUT /actividades/1
   {
     "estado": "COMPLETADA",
     "fecha_fin": "2025-10-03T17:00:00"
   }
   ```

   **Intentar valor invalido (ERROR)**:
   ```json
   PUT /actividades/1
   {
     "estado": "TERMINADA"
   }
   ```

   **Response de error**:
   ```json
   {
     "detail": [
       {
         "type": "enum",
         "loc": ["body", "estado"],
         "msg": "Input should be 'PENDIENTE', 'EN_PROCESO', 'COMPLETADA' or 'CANCELADA'",
         "input": "TERMINADA"
       }
     ]
   }
   ```

7. **Obtener valores posibles del ENUM**:
   ```
   GET /actividades/enums/estados-actividad
   ```

   **Response**:
   ```json
   {
     "estados": [
       "PENDIENTE",
       "EN_PROCESO",
       "COMPLETADA",
       "CANCELADA"
     ]
   }
   ```

---

## Puntos Clave del Patron

### 1. BaseRepository Constructor
```python
# CORRECTO
super().__init__(Model, db)

# INCORRECTO
super().__init__(db, Model)
```

### 2. Campos de Auditoria (SIEMPRE incluir)
```python
is_active = Column(Boolean, default=True, nullable=False)
is_deleted = Column(Boolean, default=False, nullable=False)
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### 3. Soft Delete (filtrar en consultas)
```python
# SIEMPRE filtrar is_deleted
query.filter(Model.is_deleted == False)
```

### 4. Relaciones Bidireccionales
```python
# En Tecnico
actividades = relationship("Actividad", back_populates="tecnico")

# En Actividad
tecnico = relationship("Tecnico", back_populates="actividades")
```

### 5. Validaciones en Service
```python
# Validaciones de negocio van en Service, NO en Repository
if fecha_inicio > fecha_fin:
    raise EntityValidationError(...)
```

### 6. Excepciones Custom
```python
# Usar excepciones de app/shared/exceptions.py
raise EntityNotFoundError("Tecnico", tecnico_id)
raise EntityAlreadyExistsError("Actividad", "codigo", codigo)
raise EntityValidationError("Actividad", {"fecha": "Error"})
```

### 7. Pydantic v2
```python
# ConfigDict en lugar de Config
model_config = ConfigDict(from_attributes=True)

# model_dump en lugar de dict()
update_data = schema.model_dump(exclude_unset=True)
```

### 8. Enums
```python
# Definir en Model
class EstadoEnum(str, enum.Enum):
    VALOR1 = "VALOR1"

# Usar en columna
estado = Column(SQLEnum(EstadoEnum), default=EstadoEnum.VALOR1)
```

### 9. POST comun vs POST with user (Entidades de Personal)

**REGLA**: Para entidades que representan personal/usuarios del sistema, SIEMPRE implementar ambos endpoints.

**POST comun** (`POST /tecnicos/`):
- Usar cuando el usuario YA EXISTE en el sistema
- Requiere `user_id` en el request
- Caso de uso: Agregar un rol adicional a un usuario existente

```python
# Schema
class TecnicoCreate(TecnicoBase):
    user_id: int  # Usuario existente
```

**POST with user** (`POST /tecnicos/with-user`):
- Usar cuando el usuario NO EXISTE y debe crearse
- Requiere datos del usuario (email, password, username)
- Caso de uso: Registro de nuevo empleado/tecnico
- Crea AMBOS registros en una transaccion

```python
# Schema
class TecnicoCreateWithUser(TecnicoBase):
    user_email: str
    user_password: str
    user_username: Optional[str]

# Service - Transaccion atomica
def create_tecnico_with_user(self, tecnico_data, user_data):
    # Crear usuario primero
    new_user = User(...)
    self.db.add(new_user)
    self.db.flush()  # Obtener ID sin commit

    # Crear tecnico asociado
    tecnico = Tecnico(user_id=new_user.id, ...)
    self.repository.create(tecnico)
    self.db.commit()  # Commit de ambos
    return tecnico
```

**Cuando usar cada uno**:
- POST comun: Usuario login con multiples roles (admin que tambien es tecnico)
- POST with user: Registro inicial de empleado nuevo
- Ambos garantizan integridad referencial con User

---

## Ejemplos de Enums Comunes

### Ejemplo 1: Estado de Registro (Simple)

```python
# En models/entidad.py
import enum
from sqlalchemy import Enum as SQLEnum

class EstadoRegistro(str, enum.Enum):
    """Estados basicos de un registro."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"

# En el modelo
estado = Column(SQLEnum(EstadoRegistro), default=EstadoRegistro.ACTIVO, nullable=False)
```

```python
# En schemas/entidad_schemas.py
from enum import Enum

class EstadoRegistroEnum(str, Enum):
    """Estados para schema."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"

# En schema
estado: EstadoRegistroEnum = Field(default=EstadoRegistroEnum.ACTIVO)
```

### Ejemplo 2: Prioridad

```python
# Model
class Prioridad(str, enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"

prioridad = Column(SQLEnum(Prioridad), default=Prioridad.MEDIA, nullable=False)
```

```python
# Schema
class PrioridadEnum(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"

prioridad: PrioridadEnum = Field(default=PrioridadEnum.MEDIA)
```

### Ejemplo 3: Tipo de Documento

```python
# Model
class TipoDocumento(str, enum.Enum):
    CEDULA = "CEDULA"
    PASAPORTE = "PASAPORTE"
    RUT = "RUT"
    NIT = "NIT"
    CEDULA_EXTRANJERIA = "CEDULA_EXTRANJERIA"
    OTRO = "OTRO"

tipo_documento = Column(SQLEnum(TipoDocumento), nullable=False)
```

```python
# Schema
class TipoDocumentoEnum(str, Enum):
    CEDULA = "CEDULA"
    PASAPORTE = "PASAPORTE"
    RUT = "RUT"
    NIT = "NIT"
    CEDULA_EXTRANJERIA = "CEDULA_EXTRANJERIA"
    OTRO = "OTRO"

tipo_documento: TipoDocumentoEnum = Field(...)
```

### Ejemplo 4: Tipo de Usuario con Permisos

```python
# Model
class TipoUsuario(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    SUPERVISOR = "SUPERVISOR"
    OPERADOR = "OPERADOR"
    CLIENTE = "CLIENTE"
    INVITADO = "INVITADO"

tipo_usuario = Column(SQLEnum(TipoUsuario), default=TipoUsuario.OPERADOR, nullable=False)
```

```python
# Schema
class TipoUsuarioEnum(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    SUPERVISOR = "SUPERVISOR"
    OPERADOR = "OPERADOR"
    CLIENTE = "CLIENTE"
    INVITADO = "INVITADO"

tipo_usuario: TipoUsuarioEnum = Field(default=TipoUsuarioEnum.OPERADOR)
```

### Ejemplo 5: Estado de Proceso (Complejo)

```python
# Model
class EstadoProceso(str, enum.Enum):
    INICIADO = "INICIADO"
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"
    EN_ESPERA = "EN_ESPERA"

estado_proceso = Column(SQLEnum(EstadoProceso), default=EstadoProceso.INICIADO, nullable=False)
```

```python
# Schema
class EstadoProcesoEnum(str, Enum):
    INICIADO = "INICIADO"
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"
    EN_ESPERA = "EN_ESPERA"

estado_proceso: EstadoProcesoEnum = Field(default=EstadoProcesoEnum.INICIADO)
```

### Ejemplo 6: Categoria de Producto

```python
# Model
class CategoriaProducto(str, enum.Enum):
    ELECTRONICA = "ELECTRONICA"
    ROPA = "ROPA"
    ALIMENTOS = "ALIMENTOS"
    HOGAR = "HOGAR"
    DEPORTES = "DEPORTES"
    LIBROS = "LIBROS"
    OTROS = "OTROS"

categoria = Column(SQLEnum(CategoriaProducto), nullable=False)
```

```python
# Schema
class CategoriaProductoEnum(str, Enum):
    ELECTRONICA = "ELECTRONICA"
    ROPA = "ROPA"
    ALIMENTOS = "ALIMENTOS"
    HOGAR = "HOGAR"
    DEPORTES = "DEPORTES"
    LIBROS = "LIBROS"
    OTROS = "OTROS"

categoria: CategoriaProductoEnum = Field(...)
```

### Ejemplo 7: Metodo de Pago

```python
# Model
class MetodoPago(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    TRANSFERENCIA = "TRANSFERENCIA"
    PSE = "PSE"
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"

metodo_pago = Column(SQLEnum(MetodoPago), nullable=False)
```

```python
# Schema
class MetodoPagoEnum(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    TRANSFERENCIA = "TRANSFERENCIA"
    PSE = "PSE"
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"

metodo_pago: MetodoPagoEnum = Field(...)
```

### Ejemplo 8: Nivel de Acceso

```python
# Model
class NivelAcceso(str, enum.Enum):
    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    RESTRINGIDO = "RESTRINGIDO"
    CONFIDENCIAL = "CONFIDENCIAL"

nivel_acceso = Column(SQLEnum(NivelAcceso), default=NivelAcceso.PRIVADO, nullable=False)
```

```python
# Schema
class NivelAccesoEnum(str, Enum):
    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    RESTRINGIDO = "RESTRINGIDO"
    CONFIDENCIAL = "CONFIDENCIAL"

nivel_acceso: NivelAccesoEnum = Field(default=NivelAccesoEnum.PRIVADO)
```

### Endpoint para Obtener Valores de Enum

```python
# En router
@router.get("/enums/estados-actividad", tags=["Enums"])
def get_estados_actividad():
    """Obtiene los valores posibles para estado de actividad."""
    return {
        "estados": [estado.value for estado in ActividadEstado]
    }
```

### Validacion de Enum en Service

```python
def update_estado(self, actividad_id: int, nuevo_estado: str) -> Actividad:
    """Actualiza el estado de una actividad con validacion."""
    actividad = self.get_actividad(actividad_id)

    # Validar que el estado sea valido
    try:
        estado_enum = ActividadEstado(nuevo_estado.upper())
    except ValueError:
        raise EntityValidationError("Actividad", {
            "estado": f"Estado invalido. Valores permitidos: {[e.value for e in ActividadEstado]}"
        })

    # Validar transiciones de estado (logica de negocio)
    if actividad.estado == ActividadEstado.COMPLETADA and estado_enum != ActividadEstado.COMPLETADA:
        raise EntityValidationError("Actividad", {
            "estado": "No se puede cambiar el estado de una actividad completada"
        })

    actividad.estado = estado_enum
    self.repository.update(actividad, {"estado": estado_enum})
    return actividad
```

---

## Checklist de Implementacion

Para agregar una nueva entidad, seguir estos pasos:

- [ ] Crear carpeta `app/entities/<entidad>/`
- [ ] Crear subcarpetas: models, schemas, repositories, services, controllers, routers
- [ ] Implementar Model con campos de auditoria
- [ ] Implementar Schemas (Base, Create, Update, Response, ListResponse)
- [ ] Implementar Repository heredando de BaseRepository
- [ ] Implementar Service con validaciones de negocio
- [ ] Implementar Controller
- [ ] Definir permisos en `permissions_seed_data.py` (5 CRUD + customs)
- [ ] Asignar permisos a roles en `TEMPLATE_PERMISSION_MATRIX`
- [ ] Implementar Router con `Depends(require_permission(entity, action))`
- [ ] Registrar router en main.py
- [ ] Re-sincronizar base de datos (truncate permisos + restart server)
- [ ] Probar endpoints en Swagger con diferentes roles
- [ ] Crear tests unitarios (opcional)

---

## Comandos Utiles

**Iniciar servidor**:
```bash
python main.py
```

**Crear tablas**:
```bash
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

**Truncar base de datos**:
```bash
python truncate_db.py
```

**Ver documentacion**:
```
http://localhost:8001/docs
```

**Obtener token**:
```bash
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@tuempresa.com&password=root" \
  http://localhost:8001/token
```

---

## Archivos de Referencia

- **BaseRepository**: `app/shared/base_repository.py`
- **Excepciones**: `app/shared/exceptions.py`
- **Dependencias**: `app/shared/dependencies.py`
- **Ejemplo completo**: `app/entities/individuals/`
- **Ejemplo geografico**: `app/entities/countries/` y `app/entities/states/`
- **Guia detallada**: `ADDING_ENTITIES.md`

---

**Fecha**: 2025-10-02
**Mantenido por**: Eric Guzman
#!/usr/bin/env python
"""
CLI de Utilidades para FastAPI Template

Script consolidado para tareas comunes de desarrollo y administración.

Uso:
    python scripts.py genkey         - Generar claves seguras
    python scripts.py createdb       - Crear base de datos PostgreSQL
    python scripts.py start          - Iniciar servidor
    python scripts.py restart        - Reiniciar servidor
    python scripts.py truncate       - Truncar base de datos (metodo seguro)
    python scripts.py truncate-hard  - Truncar base de datos (metodo alternativo)
    python scripts.py autodiscover   - Escanear endpoints y sincronizar permisos
    python scripts.py cleanup-perms  - Limpiar permisos temporales expirados
    python scripts.py verify-perms   - Verificar permisos efectivos de un usuario
    python scripts.py grant-perm     - Otorgar permiso temporal a usuario
    python scripts.py help           - Mostrar ayuda

Autor: E. Guzman
"""

import sys
import os
import secrets
import string
import subprocess
import time
import socket
import re
from typing import Optional
from getpass import getpass

# ==================== COMANDO: GENERAR CLAVES ====================

def generate_secret_key(length: int = 32) -> str:
    """Genera SECRET_KEY segura para JWT."""
    return secrets.token_urlsafe(length)


def generate_secure_password(length: int = 16) -> str:
    """Genera contraseña segura con caracteres alfanumericos y especiales."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_database_password(length: int = 20) -> str:
    """Genera contraseña para base de datos (sin caracteres especiales problematicos)."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def cmd_genkey():
    """Genera claves seguras para produccion."""
    print("=" * 60)
    print("GENERADOR DE CLAVES SEGURAS - API TEMPLATE")
    print("=" * 60)

    print("\nPARA ACTUALIZAR .env EN PRODUCCION:")
    print("-" * 40)

    secret_key = generate_secret_key(32)
    db_password = generate_database_password(20)
    admin_password = generate_secure_password(12)

    print(f"SECRET_KEY={secret_key}")
    print(f"DATABASE_URL=postgresql://postgres:{db_password}@localhost:5432/tu_db")
    print(f"DEFAULT_ADMIN_PASSWORD={admin_password}")

    print("\nIMPORTANTE:")
    print("   1. Guarda estas claves en un lugar seguro")
    print("   2. Nunca compartas el SECRET_KEY")
    print("   3. Cambia la contraseña de PostgreSQL en tu servidor")
    print("   4. Actualiza .env con estos valores")
    print("   5. Reinicia la aplicacion despues del cambio")

    print("\nDESARROLLO:")
    print("   Para desarrollo, puedes mantener los valores actuales")
    print("   Usa estas claves solo en PRODUCCION")

    print("\n" + "=" * 60)


# ==================== COMANDO: CREAR BASE DE DATOS ====================

def normalize_db_name(name: str) -> str:
    """Normaliza el nombre de la base de datos según las reglas."""
    # Reemplazar espacios por guiones bajos
    name = name.replace(" ", "_")
    # Convertir a MAYÚSCULAS
    name = name.upper()
    # Remover caracteres no permitidos (solo permitir letras, números y guiones bajos)
    name = ''.join(c for c in name if c.isalnum() or c == '_')
    return name


def get_db_credentials():
    """Solicita las credenciales de PostgreSQL al usuario."""
    print("=" * 60)
    print("CREACIÓN DE BASE DE DATOS")
    print("=" * 60)
    print()
    print("Ingresa los datos de conexión a PostgreSQL.")
    print("Presiona ENTER para usar los valores por defecto.")
    print()

    # Solicitar nombre de la base de datos
    print("Nombre de la base de datos:")
    print("  - Se agregará el prefijo 'bpta_db_' automáticamente")
    print("  - Espacios serán reemplazados por '_'")
    print("  - Se convertirá a MAYÚSCULAS automáticamente")
    db_suffix = input("Nombre [TEST_TEMPLATE]: ").strip() or "TEST_TEMPLATE"

    # Normalizar y construir el nombre completo
    db_suffix_normalized = normalize_db_name(db_suffix)
    db_name = f"bpta_db_{db_suffix_normalized}"

    print(f"\n[OK] Nombre final de la base de datos: {db_name}")
    print()

    host = input("Host de PostgreSQL [localhost]: ").strip() or "localhost"
    port = input("Puerto [5432]: ").strip() or "5432"
    username = input("Usuario de PostgreSQL [postgres]: ").strip() or "postgres"
    print("Contraseña de PostgreSQL (ENTER si está vacía):")
    password = getpass("")

    # Validar puerto
    try:
        port = int(port)
    except ValueError:
        print("Error: El puerto debe ser un número.")
        sys.exit(1)

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "db_name": db_name
    }


def create_database(credentials):
    """Crea la base de datos con el nombre especificado si no existe."""
    try:
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("\n Error: psycopg2 no está instalado.")
        print("   Instálalo con: pip install psycopg2-binary")
        return False

    db_name = credentials['db_name']

    try:
        print(f"\n Conectando a PostgreSQL en {credentials['host']}:{credentials['port']}...")

        # Conectar al servidor PostgreSQL (base de datos 'postgres' por defecto)
        conn = psycopg2.connect(
            host=credentials['host'],
            port=credentials['port'],
            user=credentials['username'],
            password=credentials['password'],
            database='postgres'  # Conectar a la base de datos por defecto
        )

        # Configurar para permitir CREATE DATABASE
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Verificar si la base de datos existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f" La base de datos '{db_name}' ya existe.")
            cursor.close()
            conn.close()
            return True

        # Crear la base de datos
        print(Colors.info(f"[INFO] Creando base de datos '{db_name}'..."))
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_name)
        ))
        print(Colors.success(f"[OK] Base de datos '{db_name}' creada exitosamente."))

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n Error: {e}")
        print("\nVerifica que:")
        print("  - PostgreSQL esté corriendo")
        print("  - Las credenciales sean correctas")
        print("  - El host y puerto sean correctos")
        return False


def update_env_files(credentials):
    """Actualiza los archivos .env y .env.example con la nueva DATABASE_URL."""
    print("\n" + "=" * 60)
    print("Actualización de archivos de configuración")
    print("=" * 60)
    print("\nEsto actualizará la variable DATABASE_URL en .env y .env.example")
    print("con las credenciales que acabas de proporcionar.")
    print()
    response = input("¿Deseas actualizar los archivos? (s/n) [s]: ").strip().lower() or 's'

    if response not in ['s', 'si', 'y', 'yes']:
        print(" Archivos .env no fueron modificados.")
        return

    # Construir la nueva DATABASE_URL con el nombre de base de datos personalizado
    new_database_url = (
        f"postgresql://{credentials['username']}:{credentials['password']}"
        f"@{credentials['host']}:{credentials['port']}/{credentials['db_name']}"
    )

    # Patrón para buscar la línea DATABASE_URL
    pattern = re.compile(r'^DATABASE_URL\s*=\s*.*$', re.MULTILINE)
    replacement = f"DATABASE_URL={new_database_url}"

    files_to_update = ['.env', '.env.example']
    updated_files = []

    for filename in files_to_update:
        filepath = os.path.join(os.path.dirname(__file__), filename)

        if not os.path.exists(filepath):
            print(f"  Archivo {filename} no encontrado, omitiendo...")
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Reemplazar la línea DATABASE_URL
            if 'DATABASE_URL' in content:
                new_content = pattern.sub(replacement, content)

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                updated_files.append(filename)
                print(f" Archivo {filename} actualizado correctamente.")
            else:
                print(f" DATABASE_URL no encontrada en {filename}, omitiendo...")

        except Exception as e:
            print(f" Error al actualizar {filename}: {e}")

    if updated_files:
        print(f"\n Archivos actualizados: {', '.join(updated_files)}")
        print(f" Nueva DATABASE_URL: {new_database_url}")
    else:
        print("\n No se actualizó ningún archivo.")


def cmd_createdb():
    """Crea la base de datos PostgreSQL."""
    try:
        # Obtener credenciales
        credentials = get_db_credentials()

        # Crear base de datos
        success = create_database(credentials)

        if not success:
            print("\n No se pudo crear la base de datos.")
            sys.exit(1)

        # Preguntar si desea actualizar archivos .env
        update_env_files(credentials)

        print("\n" + "=" * 60)
        print(" Proceso completado exitosamente.")
        print("=" * 60)
        print("\nPróximos pasos:")
        print("  1. Ejecuta 'python main.py' para iniciar el servidor")
        print("  2. Las tablas se crearán automáticamente al iniciar")
        print("  3. Accede a http://localhost:8001/docs para ver la API")
        print()

    except KeyboardInterrupt:
        print("\n\n  Proceso cancelado por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n Error inesperado: {e}")
        sys.exit(1)


# ==================== COMANDO: INICIAR SERVIDOR ====================

def find_free_port(start_port: int = 8000) -> Optional[int]:
    """Encuentra un puerto libre comenzando desde start_port."""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def kill_python_processes():
    """Mata todos los procesos Python."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "python.exe"],
            capture_output=True,
            text=True
        )
        print("Procesos Python terminados")
        time.sleep(2)
    except Exception as e:
        print(f"Error matando procesos: {e}")


def cmd_start():
    """Inicia el servidor en un puerto libre."""
    # Encontrar puerto libre
    port = find_free_port(8000)
    if not port:
        print("Error: No se encontro puerto libre")
        sys.exit(1)

    print(f"Puerto libre encontrado: {port}")
    print(f"Servidor estara disponible en: http://127.0.0.1:{port}")
    print(f"Swagger UI: http://127.0.0.1:{port}/docs")
    print("\nIniciando servidor...")

    try:
        subprocess.run([
            sys.executable, "-c",
            f"""
import uvicorn
from main import app
uvicorn.run(app, host='127.0.0.1', port={port})
"""
        ])
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")


# ==================== COMANDO: REINICIAR SERVIDOR ====================

def cmd_restart():
    """Reinicia el servidor automaticamente."""
    print("Reiniciando servidor...")

    # Verificar si psutil esta disponible
    try:
        import psutil

        print("\nBuscando procesos Python en puerto 8001...")
        killed = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('main.py' in str(arg) for arg in cmdline):
                        print(f"   Matando proceso {proc.info['pid']}: {' '.join(cmdline)}")
                        proc.kill()
                        killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if killed > 0:
            print(f"OK: {killed} proceso(s) terminado(s)")
            time.sleep(2)
        else:
            print("OK: No hay procesos previos corriendo")

    except ImportError:
        print("Advertencia: psutil no disponible, usando metodo alternativo...")
        kill_python_processes()

    # Iniciar servidor nuevo
    print("\nIniciando servidor nuevo...")
    print("=" * 60)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except Exception as e:
        print(f"\nError al iniciar servidor: {e}")


# ==================== COMANDO: TRUNCAR BD ====================

def cmd_truncate():
    """Truncar base de datos usando metodo seguro (DROP SCHEMA CASCADE)."""
    try:
        from database import engine
        from sqlalchemy import text

        print("Advertencia: Esto eliminara TODAS las tablas de la base de datos")
        confirm = input("Escribe 'CONFIRMAR' para continuar: ")

        if confirm != "CONFIRMAR":
            print("Operacion cancelada")
            return

        print("\nEliminando todas las tablas...")

        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()

        print("Todas las tablas eliminadas exitosamente")
        print("Las tablas se recrearan automaticamente en el siguiente inicio del servidor")
        print("\nEjecuta: python main.py")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_truncate_hard():
    """Truncar base de datos usando metodo alternativo (DROP TABLE por tabla)."""
    try:
        from sqlalchemy import create_engine, text
        import os
        from dotenv import load_dotenv

        load_dotenv()

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/api_demo_db")

        print("Advertencia: Esto eliminara TODAS las tablas de la base de datos")
        print(f"Base de datos: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")
        confirm = input("Escribe 'CONFIRMAR' para continuar: ")

        if confirm != "CONFIRMAR":
            print("Operacion cancelada")
            return

        print("\nConectando a la base de datos...")
        engine = create_engine(DATABASE_URL)

        print("Eliminando todas las tablas...")
        with engine.connect() as conn:
            # Desactivar foreign keys
            conn.execute(text("SET session_replication_role = 'replica';"))
            conn.commit()

            # Obtener todas las tablas
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]

            print(f"Tablas encontradas: {len(tables)}")

            # Eliminar cada tabla
            for table in tables:
                print(f"  Eliminando {table}...")
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

            conn.commit()

            # Reactivar foreign keys
            conn.execute(text("SET session_replication_role = 'origin';"))
            conn.commit()

        print("Base de datos truncada exitosamente!")
        print("\nEjecuta: python main.py")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# ==================== COMANDO: AUTODISCOVERY DE PERMISOS ====================

def cmd_autodiscover():
    """Escanea endpoints y sincroniza permisos en la base de datos."""
    print("=" * 60)
    print("AUTODISCOVERY DE PERMISOS - PHASE 2")
    print("=" * 60)

    # Verificar si es dry-run
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("\nMODO: DRY RUN (solo visualizacion, sin cambios)")
    else:
        print("\nMODO: PRODUCCION (aplicara cambios a la base de datos)")

    print("\nCargando aplicacion FastAPI...")

    try:
        # Importar la aplicacion y dependencias
        from main import app
        from database import SessionLocal
        from app.shared.autodiscover_permissions import discover_endpoints, sync_permissions_to_db

        # Crear sesion de base de datos
        db = SessionLocal()

        print("OK: Aplicacion cargada correctamente")
        print(f"OK: Rutas registradas: {len([r for r in app.routes])}")

        # Descubrir endpoints
        print("\nEscaneando endpoints...")
        discovered = discover_endpoints(app)
        print(f"OK: {len(discovered)} endpoints descubiertos")

        # Mostrar resumen por entidad
        entities = {}
        for perm in discovered:
            entity = perm["entity"]
            if entity not in entities:
                entities[entity] = []
            entities[entity].append(perm["action"])

        print("\nResumen por entidad:")
        for entity, actions in sorted(entities.items()):
            unique_actions = set(actions)
            print(f"  - {entity}: {len(actions)} endpoints ({', '.join(sorted(unique_actions))})")

        # Sincronizar con base de datos
        print("\nSincronizando con base de datos...")
        stats = sync_permissions_to_db(discovered, db, dry_run=dry_run)

        # Mostrar resultados
        print("\n" + "=" * 60)
        print("RESULTADOS")
        print("=" * 60)
        print(f"Total descubierto: {stats['total_discovered']}")
        print(f"Permisos existentes: {stats['existing']}")
        print(f"Permisos nuevos: {stats['new']}")

        if stats['new'] > 0:
            print("\nPermisos nuevos encontrados:")
            for perm in stats['new_permissions']:
                print(f"  + {perm['entity']}:{perm['action']} ({perm['http_method']} {perm['endpoint']})")
                print(f"    Descripcion: {perm['description']}")

        if dry_run:
            print("\nNOTA: Modo dry-run activo. No se aplicaron cambios.")
            print("Ejecuta sin --dry-run para aplicar los cambios:")
            print("  python scripts.py autodiscover")
        else:
            print(f"\nOK: {stats['new']} permisos agregados a la base de datos")

        print("\n" + "=" * 60)
        print("Autodiscovery completado exitosamente")
        print("=" * 60)

        # Cerrar sesion
        db.close()

    except ImportError as e:
        print(f"\nError: No se pudo importar modulo requerido")
        print(f"Detalle: {e}")
        print("\nVerifica que:")
        print("  - La aplicacion este correctamente configurada")
        print("  - La base de datos este accesible")
        print("  - Todas las dependencias esten instaladas")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ==================== COMANDO: LIMPIAR PERMISOS EXPIRADOS ====================

def cmd_cleanup_perms():
    """Limpia permisos temporales expirados (Phase 3)."""
    print("=" * 60)
    print("LIMPIEZA DE PERMISOS TEMPORALES EXPIRADOS")
    print("=" * 60)

    try:
        from database import SessionLocal
        from app.shared.services.user_permission_service import UserPermissionService

        db = SessionLocal()
        service = UserPermissionService(db)

        print("\nBuscando permisos expirados...")
        count = service.cleanup_expired_permissions()

        print(f"\n {count} permisos expirados desactivados")

        if count > 0:
            print("\nLos siguientes permisos fueron desactivados:")
            print("  - Permisos con valid_until < fecha actual")
            print("  - Estado cambiado a is_active = False")
        else:
            print(Colors.success("\n[OK] No hay permisos expirados"))

        db.close()

        print("\n" + "=" * 60)
        print("Limpieza completada exitosamente")
        print("=" * 60)

    except ImportError as e:
        print(f"\n Error: Módulo no encontrado")
        print(f"Detalle: {e}")
        print("\nVerifica que:")
        print("  - La aplicación esté correctamente configurada")
        print("  - Phase 3 esté implementada")
        sys.exit(1)
    except Exception as e:
        print(f"\n Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ==================== COMANDO: VERIFICAR PERMISOS ====================

def cmd_verify_perms():
    """Verifica permisos efectivos de un usuario (Phase 3)."""
    print("=" * 60)
    print("VERIFICACIÓN DE PERMISOS EFECTIVOS")
    print("=" * 60)

    try:
        # Solicitar user_id
        user_id_str = input("\nIngresa el ID del usuario: ").strip()

        try:
            user_id = int(user_id_str)
        except ValueError:
            print(" Error: El ID debe ser un número")
            sys.exit(1)

        from database import SessionLocal
        from app.shared.services.user_permission_service import UserPermissionService
        from database import User

        db = SessionLocal()
        service = UserPermissionService(db)

        # Verificar que el usuario existe
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"\n Error: Usuario con ID {user_id} no encontrado")
            db.close()
            sys.exit(1)

        print(f"\nUsuario: {user.name} ({user.email})")
        print(f"Rol: {user.role}")

        # Obtener permisos efectivos
        print("\n Obteniendo permisos efectivos...")
        summary = service.get_effective_permissions_summary(user_id)

        # Mostrar permisos
        print("\n" + "=" * 60)
        print("PERMISOS EFECTIVOS")
        print("=" * 60)

        if not summary["permissions"]:
            print("\n Este usuario no tiene permisos asignados")
        else:
            # Agrupar por entidad
            by_entity = {}
            for perm in summary["permissions"]:
                entity = perm["entity"]
                if entity not in by_entity:
                    by_entity[entity] = []
                by_entity[entity].append(perm)

            for entity, perms in sorted(by_entity.items()):
                print(f"\n {entity.upper()}")
                print("-" * 40)

                for p in sorted(perms, key=lambda x: x["action"]):
                    level = p["effective_level"]
                    source = p["source"]

                    # Mostrar nivel con indicador coloreado
                    level_indicator = {
                        0: "[NONE]  ",
                        1: "[READ]  ",
                        2: "[UPDATE]",
                        3: "[CREATE]",
                        4: "[DELETE]"
                    }

                    level_color = {
                        0: Colors.RED,
                        1: Colors.CYAN,
                        2: Colors.YELLOW,
                        3: Colors.GREEN,
                        4: Colors.MAGENTA
                    }

                    level_name = {
                        0: "None",
                        1: "Read",
                        2: "Update",
                        3: "Create",
                        4: "Delete"
                    }

                    indicator = level_indicator.get(level, "[?]")
                    color = level_color.get(level, Colors.RESET)
                    name = level_name.get(level, "Unknown")

                    # Indicador de override
                    override_marker = " [OVERRIDE]" if p["has_override"] else ""

                    print(f"  {color}{indicator}{Colors.RESET} {p['action']:20} → Nivel {level} ({name}) - {source}{override_marker}")

                    # Mostrar expiración si es temporal
                    if p.get("override_expires"):
                        print(Colors.warning(f"     [EXPIRA] {p['override_expires']}"))

        db.close()

        print("\n" + "=" * 60)

    except ImportError as e:
        print(Colors.error(f"\n[ERROR] Módulo no encontrado"))
        print(f"Detalle: {e}")
        sys.exit(1)
    except Exception as e:
        print(Colors.error(f"\n[ERROR] Error inesperado: {e}"))
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ==================== COMANDO: OTORGAR PERMISO ====================

def cmd_grant_perm():
    """Otorga permiso temporal a un usuario (Phase 3)."""
    print("=" * 60)
    print("OTORGAR PERMISO TEMPORAL A USUARIO")
    print("=" * 60)

    try:
        # Solicitar datos
        print(Colors.info("\n[INPUT] Ingresa los datos del permiso:"))

        user_id_str = input("  User ID: ").strip()
        try:
            user_id = int(user_id_str)
        except ValueError:
            print(Colors.error("[ERROR] El ID debe ser un número"))
            sys.exit(1)

        entity = input("  Entidad (ej: companies, individuals): ").strip()
        action = input("  Acción (ej: delete, update, create): ").strip()

        level_str = input("  Nivel (0-4, donde 4=Delete, 3=Create, 2=Update, 1=Read): ").strip()
        try:
            level = int(level_str)
            if not 0 <= level <= 4:
                raise ValueError
        except ValueError:
            print(Colors.error("[ERROR] El nivel debe ser un número entre 0 y 4"))
            sys.exit(1)

        hours_str = input("  Horas de validez (ENTER para permanente): ").strip()
        hours = None
        if hours_str:
            try:
                hours = int(hours_str)
                if hours <= 0:
                    raise ValueError
            except ValueError:
                print(Colors.error("[ERROR] Las horas deben ser un número positivo"))
                sys.exit(1)

        reason = input("  Razón (opcional): ").strip() or "Otorgado vía CLI"

        # Confirmar
        print("\n" + "=" * 60)
        print("CONFIRMACIÓN")
        print("=" * 60)
        print(f"Usuario ID: {user_id}")
        print(f"Permiso: {entity}:{action}")
        print(f"Nivel: {level}")
        print(f"Duración: {'Permanente' if not hours else f'{hours} horas'}")
        print(f"Razón: {reason}")

        confirm = input("\n¿Confirmar? (s/n): ").strip().lower()
        if confirm not in ['s', 'si', 'y', 'yes']:
            print(Colors.warning("[CANCELADO] Operación cancelada"))
            sys.exit(0)

        # Otorgar permiso
        from database import SessionLocal
        from app.shared.services.user_permission_service import UserPermissionService
        from database import User

        db = SessionLocal()
        service = UserPermissionService(db)

        # Verificar que el usuario existe
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(Colors.error(f"\n[ERROR] Usuario con ID {user_id} no encontrado"))
            db.close()
            sys.exit(1)

        print(Colors.info(f"\n[PROCESANDO] Otorgando permiso a {user.name} ({user.email})..."))

        # Usar admin user (ID 1) como granted_by
        admin_id = 1

        permission = service.grant_permission_by_entity_action(
            user_id=user_id,
            entity=entity,
            action=action,
            level=level,
            granted_by_user_id=admin_id,
            hours=hours,
            reason=reason
        )

        print(Colors.success(f"\n[OK] Permiso otorgado exitosamente"))
        print(f"   ID del permiso: {permission.id}")

        if permission.valid_until:
            print(f"   Válido hasta: {permission.valid_until}")
        else:
            print(f"   Válido: Permanente")

        db.close()

        print("\n" + "=" * 60)
        print("Operación completada")
        print("=" * 60)

    except ImportError as e:
        print(Colors.error(f"\n[ERROR] Módulo no encontrado"))
        print(f"Detalle: {e}")
        print("\nVerifica que Phase 3 esté implementada")
        sys.exit(1)
    except Exception as e:
        print(Colors.error(f"\n[ERROR] {e}"))
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ==================== COMANDO: AYUDA ====================

def cmd_help():
    """Muestra ayuda de comandos disponibles."""
    print(__doc__)


# ==================== MAIN ====================

def main():
    """Punto de entrada principal del CLI."""
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    commands = {
        'genkey': cmd_genkey,
        'createdb': cmd_createdb,
        'start': cmd_start,
        'restart': cmd_restart,
        'truncate': cmd_truncate,
        'truncate-hard': cmd_truncate_hard,
        'autodiscover': cmd_autodiscover,
        'cleanup-perms': cmd_cleanup_perms,
        'verify-perms': cmd_verify_perms,
        'grant-perm': cmd_grant_perm,
        'help': cmd_help,
        '--help': cmd_help,
        '-h': cmd_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Error: Comando desconocido '{command}'")
        print("\nComandos disponibles:")
        print("  genkey         - Generar claves seguras")
        print("  createdb       - Crear base de datos PostgreSQL")
        print("  start          - Iniciar servidor")
        print("  restart        - Reiniciar servidor")
        print("  truncate       - Truncar base de datos (metodo seguro)")
        print("  truncate-hard  - Truncar base de datos (metodo alternativo)")
        print("  autodiscover   - Escanear endpoints y sincronizar permisos")
        print("  cleanup-perms  - Limpiar permisos temporales expirados")
        print("  verify-perms   - Verificar permisos efectivos de un usuario")
        print("  grant-perm     - Otorgar permiso temporal a usuario")
        print("  help           - Mostrar ayuda")
        sys.exit(1)


if __name__ == "__main__":
    main()
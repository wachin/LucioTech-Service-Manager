# AGENTS.md

Instrucciones para agentes de IA que trabajen en este repositorio. Léelas antes de tocar código.

## Proyecto

**LucioTech Service Manager**: aplicación de escritorio en Python 3 y PyQt6 para registrar recepción, diagnóstico, reparación y entrega de equipos del servicio técnico del Ing. Lucio. Debe funcionar sin conexión y no enviar datos a servidores externos.

La especificación completa está en `ROADMAP.md`. Es la fuente de verdad para requisitos, esquema y estados de avance.

## Reglas obligatorias

1. **No instalar paquetes.** El usuario instala las dependencias en el `.venv`. Si falta algo, detente y da el comando exacto (`pip install <paquete>`). Las consultas de solo lectura (`pip show`, `python -c "import ..."`) sí están permitidas.
2. **Trabajar siempre dentro del `.venv`.** Ejecuta pruebas con `.venv/bin/python -m pytest`.
3. **No hacer commit ni push.** El usuario revisa y hace los commits. Solo prepara el cambio y reporta.
4. **Un paso de la Fase 1 por bloque.** Escribe código, pruebas y ejecuta la suite completa en la misma respuesta.
5. **No marcar casillas `[x]` del ROADMAP** hasta que la tarea esté implementada, probada y ejecutada. Si está incompleta, usa `[~]`.
6. **No avanzar de fase** si quedan casillas pendientes en la anterior (ROADMAP §0).
7. **No registrar contraseñas ni PIN** en logs, mensajes ni salidas de comandos.
8. **Ocultar secretos al inspeccionar configuración.** Nunca imprimir API keys ni contraseñas completas.

## Comandos

```bash
# Activar el entorno (desde la raíz del proyecto)
source .venv/bin/activate

# Pruebas completas
.venv/bin/python -m pytest

# Migraciones (la base por defecto está en ~/.local/share/luciotech-service-manager/)
.venv/bin/alembic upgrade head

# Base temporal para pruebas manuales (no toca datos reales)
LUCIOTECH_DATABASE_URL=sqlite:////tmp/luciotech-test.sqlite3 .venv/bin/alembic upgrade head
```

La aplicación aún no tiene punto de entrada (`luciotech.main` llegará en el paso 5).

## Estructura

```text
src/luciotech/
├── config.py                 # Nombre, app_id, organización, versión, IVA por defecto
├── database/
│   ├── connection.py         # Motor SQLite, PRAGMA foreign_keys=ON
│   ├── enums.py              # Estados, prioridades, tipos (una sola definición)
│   ├── models.py             # Modelos SQLAlchemy
│   ├── repositories.py       # CRUD por entidad (solo flush, sin commit)
│   └── migrations/           # Alembic; versiones en versions/
├── services/                 # Reglas de negocio; reciben la sesión, no hacen commit
│   ├── order_number_service.py   # OT-AAAA-NNNNNN con tabla secuencias
│   ├── totals_service.py         # Fórmula única de totales, IVA y saldo
│   ├── state_service.py          # Cambio de estado con historial automático
│   ├── order_service.py          # Creación y borrado lógico de órdenes
│   ├── settings_service.py       # Tabla configuracion (clave/valor)
│   ├── customer_service.py       # Duplicados por identificación o teléfono
│   └── equipment_service.py      # Advertencia por número de serie repetido
└── utils/
    ├── paths.py              # Rutas XDG de datos y logs
    └── validators.py         # Cédula ecuatoriana (módulo 10)
tests/                        # pytest; base temporal por prueba
```

## Convenciones de código

- Usar `from __future__ import annotations` y anotaciones de tipo.
- Docstrings en español en módulos y funciones públicas.
- Importes monetarios con `Decimal`, nunca `float`. Redondeo a centavos con `ROUND_HALF_UP`.
- Consultas solo con SQLAlchemy. No concatenar SQL.
- La UI nunca escribe SQL directamente; pasa por servicios o repositorios.
- Textos visibles al usuario en español y envueltos en `self.tr(...)` cuando haya UI (§21).
- Sin comentarios salvo que expliquen un porqué no evidente.

## Reglas de dominio que no se deben romper

- **Cédula:** módulo 10. No aplicar módulo 11 (eso es para la clave de acceso de facturas).
- **Número de orden:** formato `OT-AAAA-NNNNNN`, generado con la tabla `secuencias` dentro de la transacción. No usar `MAX(id)+1`.
- **Totales:** solo en `totals_service.py`. Fórmula en ROADMAP §5.3.
- **IVA:** 15% por defecto desde `config.py`, editable y desactivable. No dejar el 15 fijo en la lógica.
- **Historial de estados:** se crea automáticamente en cada cambio y nunca se borra al editar.
- **Borrado:** lógico (`activo=False`, `fecha_eliminacion`). Cancelar un servicio no es borrarlo.
- **Número de serie repetido:** advertencia no bloqueante.

## Datos y ficheros locales

Las rutas de datos son XDG (`~/.local/share/...` y `~/.local/state/.../logs/`). Nunca commitear datos reales de clientes.

### Reglas de `.gitignore` que conviene conocer

- `logs/` ignora **cualquier carpeta llamada `logs`** en el proyecto, no solo la raíz. Si se crea un paquete o módulo con ese nombre dentro de `src/`, cambia la regla a `/logs/` para no ignorarlo por error.
- `*.sqlite3`, `*.sqlite` y `*.db` impiden versionar bases de datos.
- `attachments/` y `backups/` impiden versionar fotos de equipos y copias de seguridad.
- Los temporales de Kate (`*~`, `*.kate-swp`, `.kateproject`, `.kateconfig`) están ignorados.
- Si un archivo ignorado ya estaba versionado, quítalo del índice con `git rm --cached`, sin borrarlo del disco. Si el archivo nuevo debe versionarse, revisa antes si una regla lo excluye (`git check-ignore -v <ruta>`).

## Documentación que debe mantenerse

- `README.md`: actualizar cuando cambie el comportamiento visible para el usuario.
- `ROADMAP.md`: actualizar casillas al terminar cada tarea y fase.
- Este archivo: actualizar cuando cambien comandos, estructura o reglas.

## Estado actual

- Fase 1, pasos 1 a 8 implementados y probados (157 pruebas): núcleo de datos, servicios, ventana principal, panel de inicio, clientes, equipos, recepción con selección de equipo existente, lista de órdenes y detalle de orden con cuatro pestañas.
- Pendiente de la Fase 1: fotografías, presupuesto y PDF. Las casillas del ROADMAP se marcan según §0 al cerrar la fase.
- `pytest-qt==4.5.0` ya está instalado en el `.venv`.
- El punto de entrada es `luciotech.main`; ejecútalo con `PYTHONPATH=src` o con el paquete instalado.

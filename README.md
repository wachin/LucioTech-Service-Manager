# LucioTech Service Manager

Aplicación de escritorio en Python 3 y PyQt6 para registrar la recepción, el diagnóstico, la reparación y la entrega de equipos tecnológicos en el servicio técnico del **Ing. Lucio**.

La aplicación funciona completamente sin conexión y no envía datos a servidores externos.

> Estado: **Fase 1 en desarrollo** (núcleo ejecutable). Consulta `ROADMAP.md` para el detalle del avance.

## Requisitos

- Debian, Ubuntu, MX Linux o derivados (Windows está previsto, pero aún no está probado).
- Python 3.11 o superior.
- Paquetes del sistema necesarios para PyQt6 en Linux, si tu distribución no los trae: consulta la documentación de PyQt6.

## Instalación en entorno virtual

Ejecuta estos comandos desde la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

La ventana principal aún no está implementada; llegará en el paso 5 de la Fase 1.

## Pruebas

Con el entorno virtual activado:

```bash
pytest
```

## Estructura del proyecto

```text
.
├── pyproject.toml
├── requirements.txt
├── README.md
├── ROADMAP.md
├── LICENSE
├── src/
│   └── luciotech/
│       ├── config.py        # Nombre, app_id, organización y versión
│       └── utils/
│           └── paths.py     # Rutas de datos y registros
└── tests/
```

## Ubicación de datos

En Linux se usan las rutas XDG:

| Contenido | Ruta |
|---|---|
| Base de datos SQLite | `~/.local/share/luciotech-service-manager/database.sqlite3` |
| Fotografías (planificado) | `~/.local/share/luciotech-service-manager/attachments/` |
| Registros (logs) | `~/.local/state/luciotech-service-manager/logs/` |

Si defines `XDG_DATA_HOME` o `XDG_STATE_HOME`, las rutas cambian en consecuencia.

## Seguridad de las contraseñas de equipos

Las contraseñas o PIN de los equipos se guardan **en texto plano** en la base de datos SQLite local. El sistema no tiene servidor, así que la protección depende de los permisos del sistema de archivos. Por eso:

- No compartas la carpeta de datos.
- Protege tu cuenta de usuario con una contraseña fuerte.
- Las contraseñas nunca se escriben en los registros.

## Solución de problemas

- **`source: no such file`**: el comando `source` debe ir en su propia línea o unido con `&&` en la misma línea. Vuelve a escribir los comandos tal como aparecen arriba.
- **`ModuleNotFoundError`**: verifica que el entorno virtual esté activado; el prompt debe mostrar `(.venv)`.

## Licencia

GPL-3.0. Consulta el archivo `LICENSE`.

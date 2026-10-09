# LucioTech Service Manager

Aplicación de escritorio en Python 3 y PyQt6 para registrar la recepción, el diagnóstico, la reparación y la entrega de equipos tecnológicos en el servicio técnico del **Ing. Lucio**.

La aplicación funciona completamente sin conexión y no envía datos a servidores externos.

> Estado: **Fase 1 en desarrollo**. Ya se puede probar la interfaz gráfica (panel de inicio, clientes, equipos y recepciones). Aún no están la vista de detalle de una orden, la edición de estados desde la interfaz ni los documentos PDF. Consulta `ROADMAP.md` para el detalle del avance.

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

Con el entorno virtual activado, desde la carpeta del proyecto:

```bash
pip install -e .
python -m luciotech.main
```

Si no quieres instalar el paquete, puedes ejecutar sin instalarlo:

```bash
PYTHONPATH=src python -m luciotech.main
```

Al arrancar, la aplicación crea la base de datos si no existe y aplica las migraciones.

La ventana principal se abre maximizada y se adapta al tamaño de la pantalla. Si la reduces, el tamaño mínimo es de 800×560 píxeles; los formularios tienen barras de desplazamiento para ver todos sus campos.

## Probar la interfaz gráfica

### Usar una base de datos de prueba

Para no mezclar datos de prueba con los datos reales, abre la aplicación con una base temporal:

```bash
LUCIOTECH_DATABASE_URL=sqlite:////tmp/luciotech-prueba.sqlite3 PYTHONPATH=src python -m luciotech.main
```

Cada vez que quieras empezar de cero, borra ese archivo antes de arrancar:

```bash
rm -f /tmp/luciotech-prueba.sqlite3
```

### Qué puedes probar

1. **Inicio:** las tarjetas muestran conteos. Con una base vacía, todas aparecen en 0 o en `0.00 USD`.
2. **Clientes:** pulsa **Nuevo cliente** y prueba:
   - dejar el nombre vacío (debe mostrar «Campo obligatorio»);
   - una cédula de 10 dígitos con dígito verificador incorrecto, como `1710034066` (debe rechazarla);
   - la cédula válida `1710034065`;
   - un teléfono con letras, como `099ABC4567` (debe rechazarlo).
   - Guarda otro cliente con el mismo teléfono en otro formato (`099 123-4567`): la aplicación debe pedir confirmación antes de guardar.
3. **Equipos:** pulsa **Nuevo equipo**. Si no hay clientes, te pedirá registrar uno primero. La contraseña se muestra oculta y el botón **Mostrar** la revela.
4. **Órdenes:** pulsa **Nueva recepción**:
   - elige un cliente existente o **Cliente nuevo** (los campos aparecen en el mismo formulario);
   - marca accesorios, escribe el problema reportado y, si quieres, un anticipo;
   - observa que el número de orden previsto es `OT-AAAA-000001` antes de guardar;
   - registra dos equipos con el mismo número de serie: debe avisar y pedir confirmación.
   - En la lista, prueba el buscador y los filtros de estado, prioridad, tipo de equipo y saldo pendiente.
5. **Atajos:** `F5` actualiza todas las pantallas y `Ctrl+Q` cierra la aplicación.
6. **Reinicio:** cierra la aplicación, vuelve a abrirla con la misma base y comprueba que los datos siguen ahí.

### Qué todavía no funciona

- No hay vista de detalle de una orden, así que no se puede cambiar su estado ni añadir pagos desde la interfaz.
- No se pueden adjuntar fotografías ni generar PDF.
- No hay copias de seguridad desde la interfaz.

### Si algo falla

Todavía no hay registro de eventos en archivo (§20 del ROADMAP). Si algo falla, ejecuta el programa desde una terminal y copia el mensaje de error completo que aparece allí.

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
- **`ModuleNotFoundError: No module named 'luciotech'`**: el paquete no está instalado. Ejecuta `pip install -e .` con el entorno virtual activado, o usa `PYTHONPATH=src` como se muestra arriba.
- **`ModuleNotFoundError` con otro nombre**: verifica que el entorno virtual esté activado; el prompt debe mostrar `(.venv)`.
- **La ventana no aparece en una sesión remota o sin pantalla**: ejecuta con `QT_QPA_PLATFORM=offscreen` solo para pruebas automáticas; no verás ventana.

## Licencia

GPL-3.0. Consulta el archivo `LICENSE`.

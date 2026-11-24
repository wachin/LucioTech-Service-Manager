#!/usr/bin/env python3
"""Genera las capturas de la interfaz para la documentación, sin tocar datos reales.

Crea una base SQLite temporal, siembra un taller de demostración y renderiza los widgets de
PyQt6 con `grab()` en modo offscreen. Los documentos se escriben con el mismo código de
impresión de la aplicación y se convierten a PNG con `pdftoppm`.

Uso, desde la raíz del proyecto:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/python tools/capture-screenshots.py

Las imágenes quedan en `docs/screenshots/`. El idioma se fuerza a inglés, que es el idioma
fuente: no se instala ningún catálogo y los textos salen tal como están en el código.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")

from PyQt6.QtCore import QLocale, Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication, QHeaderView  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from luciotech.config import APP_CONFIG, APP_VERSION  # noqa: E402
from luciotech.database.connection import (  # noqa: E402
    create_db_engine,
    create_session_factory,
)
from luciotech.database.enums import (  # noqa: E402
    BudgetLineType,
    OrderState,
    PaymentMethod,
    PaymentType,
    PhotoType,
    Priority,
    UserRole,
)
from luciotech.database.migrate import upgrade_database  # noqa: E402
from luciotech.services.budget_service import add_line, set_discount  # noqa: E402
from luciotech.services.clinical_text_service import (  # noqa: E402
    ClinicalTexts,
    save_clinical_texts,
)
from luciotech.services.customer_service import CustomerData, save_customer  # noqa: E402
from luciotech.services.equipment_service import EquipmentData  # noqa: E402
from luciotech.services.order_detail_service import (  # noqa: E402
    add_note,
    mark_delivered,
    register_payment,
)
from luciotech.services.order_service import soft_delete_order  # noqa: E402
from luciotech.services.photo_service import import_photo  # noqa: E402
from luciotech.services.reception_service import ReceptionData, register_reception  # noqa: E402
from luciotech.services.settings_service import (  # noqa: E402
    set_language,
    set_workshop_details,
)
from luciotech.services.state_service import change_order_state  # noqa: E402
from luciotech.services.user_service import (  # noqa: E402
    CurrentUser,
    create_user,
    current_user_of,
)
from luciotech.ui.dialogs.document_chooser_dialog import DocumentChooserDialog  # noqa: E402
from luciotech.ui.dialogs.login_dialog import LoginDialog  # noqa: E402
from luciotech.ui.dialogs.order_detail_dialog import OrderDetailDialog  # noqa: E402
from luciotech.ui.dialogs.reception_dialog import ReceptionDialog  # noqa: E402
from luciotech.ui.dialogs.settings_dialog import SettingsDialog  # noqa: E402
from luciotech.ui.documents import (  # noqa: E402
    DocumentKind,
    _furniture,
    document_html,
)
from luciotech.ui.main_window import MainWindow  # noqa: E402
from luciotech.ui.print_support import apply_page_setup, save_as_pdf  # noqa: E402
from luciotech.ui.translations import install_translations  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "screenshots"
SAMPLES = ROOT / "Ordenadores-de-ejemplo"

USER_ADMIN = "Ana Torres"
USER_TECH = "Luis Mora"


def _identification(prefix: str) -> str:
    """Cédula ecuatoriana válida a partir de nueve dígitos (módulo 10).

    Los datos de demostración no son de personas reales; se calcula el dígito verificador
    para que los formularios acepten la identificación sin ruido.
    """
    digits = [int(char) for char in prefix[:9]]
    check = 0
    for index, digit in enumerate(digits):
        product = digit * (2 if index % 2 == 0 else 1)
        check += product - 9 if product > 9 else product
    return prefix[:9] + str((10 - check % 10) % 10)


def _seed(session: Session) -> tuple[int, CurrentUser]:
    """Crea las cuentas, los clientes y las órdenes que aparecen en las capturas."""
    set_language(session, "en")
    set_workshop_details(
        session,
        name="Ing. Lucio · Technical Service",
        phone="+593 99 123 4567",
        email="service@luciotech.example",
        address="Av. Amazonas 1234, Quito",
    )
    create_user(
        session,
        username="ana",
        full_name=USER_ADMIN,
        password="capturas-demo-2026",
        role=UserRole.ADMINISTRADOR,
    )
    create_user(
        session,
        username="luis",
        full_name=USER_TECH,
        password="capturas-demo-2026",
        role=UserRole.TECNICO,
    )

    ana = save_customer(
        session,
        CustomerData(
            nombre_completo="Ana Torres",
            numero_identificacion=_identification("171003406"),
            telefono_principal="0991234567",
            correo_electronico="ana.torres@example.com",
            direccion="La Carolina, Quito",
        ),
    )
    marta = save_customer(
        session,
        CustomerData(
            nombre_completo="Marta Vélez",
            numero_identificacion=_identification("180245673"),
            telefono_principal="0987654321",
            correo_electronico="marta.velez@example.com",
        ),
    )
    carlos = save_customer(
        session,
        CustomerData(
            nombre_completo="Carlos Ruiz",
            numero_identificacion=_identification("092345678"),
            telefono_principal="0976543210",
        ),
    )
    luis = save_customer(
        session,
        CustomerData(
            nombre_completo="Luis Mora",
            numero_identificacion=_identification("110456789"),
            telefono_principal="0965432109",
        ),
    )
    sofia = save_customer(
        session,
        CustomerData(
            nombre_completo="Sofía Herrera",
            numero_identificacion=_identification("172345678"),
            telefono_principal="0954321098",
        ),
    )
    jorge = save_customer(
        session,
        CustomerData(
            nombre_completo="Jorge Salas",
            numero_identificacion=_identification("091234567"),
            telefono_principal="0943210987",
        ),
    )

    now = datetime.now()

    def reception(
        customer_id: int,
        *,
        kind: str,
        brand: str,
        model: str,
        serial: str,
        problem: str,
        days_ago: int,
        priority: Priority,
        diagnosis: Decimal,
        deposit: Decimal = Decimal("0"),
        technician: str = USER_ADMIN,
    ):
        return register_reception(
            session,
            ReceptionData(
                customer_id=customer_id,
                equipment=EquipmentData(
                    cliente_id=None,
                    tipo_equipo=kind,
                    marca=brand,
                    modelo=model,
                    numero_serie=serial,
                    color="Silver" if kind == "Laptop" else "Black",
                    sistema_operativo="Windows 11 Pro",
                    problema_reportado_cliente=problem,
                ),
                prioridad=priority,
                fecha_ingreso=now - timedelta(days=days_ago, hours=2),
                fecha_estimada_entrega=now + timedelta(days=2),
                costo_diagnostico=diagnosis,
                anticipo=deposit,
                tecnico_responsable=technician,
                usuario=technician,
            ),
        )

    # 1. La orden del tour: presupuesto aprobado, reparación en curso, pagos y fotos.
    focus = reception(
        ana.id,
        kind="Laptop",
        brand="HP",
        model="ProBook 450 G8",
        serial="5CD1234ABC",
        problem="Does not power on after a power surge. The customer reports a burning smell.",
        days_ago=4,
        priority=Priority.ALTA,
        diagnosis=Decimal("65"),
        deposit=Decimal("40"),
    )
    focus.equipment.accesorios_recibidos = "Cargador, Mouse, Bolso"
    focus.equipment.estado_fisico = "Light wear on the lid; screen and keyboard in good condition."
    focus.equipment.observaciones_ingreso = "Received with charger, USB mouse and laptop bag."
    add_line(
        session,
        focus,
        tipo=BudgetLineType.REPUESTO,
        descripcion="SSD 480 GB NVMe",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("65"),
    )
    add_line(
        session,
        focus,
        tipo=BudgetLineType.MANO_OBRA,
        descripcion="Motherboard diagnosis and repair",
        cantidad=Decimal("2"),
        precio_unitario=Decimal("22.50"),
    )
    add_line(
        session,
        focus,
        tipo=BudgetLineType.SERVICIO,
        descripcion="Data backup and migration",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("30"),
    )
    add_line(
        session,
        focus,
        tipo=BudgetLineType.REPUESTO,
        descripcion="DC jack and power-rail components",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("18"),
    )
    set_discount(session, focus, Decimal("15"))
    save_clinical_texts(
        session,
        focus,
        ClinicalTexts(
            diagnostico_html=(
                "<p><b>Findings</b></p>"
                "<p>The laptop does not power on. The 19 V rail is shorted to ground and the "
                "DC jack shows heat damage. The SSD is healthy and the data is readable.</p>"
                "<ul><li>Power rail: short circuit on the main board.</li>"
                "<li>DC jack: deformed by heat.</li>"
                "<li>Battery: 78 % of design capacity.</li></ul>"
            ),
            trabajo_realizado_html=(
                "<p>Replaced the damaged DC jack and the shorted capacitor on the power rail. "
                "Cleaned the board, renewed the thermal paste and installed a new 480 GB NVMe "
                "SSD. The customer's data was cloned before the repair.</p>"
                "<p>Stress test: 45 minutes at full load, stable temperatures.</p>"
            ),
            recomendaciones_html=(
                "<p>Use a surge protector and avoid charging the laptop during electrical "
                "storms. Keep the vents clear and back up important files regularly.</p>"
            ),
        ),
    )
    for state, comment in (
        (OrderState.PENDIENTE_DIAGNOSTICO, "Bench queue."),
        (OrderState.DIAGNOSTICADO, "Power rail shorted; repair is feasible."),
        (OrderState.ESPERANDO_APROBACION, "Budget sent to the customer."),
        (OrderState.EN_REPARACION, "Customer approved the budget by phone."),
    ):
        change_order_state(session, focus, state, USER_ADMIN, comment)
    register_payment(
        session,
        focus,
        tipo=PaymentType.ABONO,
        metodo=PaymentMethod.TRANSFERENCIA,
        monto=Decimal("60"),
        usuario=USER_ADMIN,
        referencia="TRX-88231",
        observaciones="Second instalment.",
    )
    add_note(
        session,
        focus,
        titulo="Customer approved the budget by phone",
        descripcion="Called at 10:15. Approved the full amount and asked to keep the old SSD.",
        usuario=USER_ADMIN,
    )
    for sample, friendly, kind, description in (
        (
            SAMPLES / "Schenker_VIA14_Laptop_asv2021-01" / "Schenker_VIA14_Laptop_asv2021-01.jpg",
            "laptop-lid-at-reception.jpg",
            PhotoType.ESTADO_AL_RECIBIR,
            "Lid and screen at reception.",
        ),
        (
            SAMPLES / "IBM_Thinkpad_R51" / "IBM_Thinkpad_R51.jpg",
            "dc-jack-detail.jpg",
            PhotoType.DANO_FISICO,
            "Reference image of the damaged DC jack area.",
        ),
    ):
        if sample.is_file():
            staged = WORK / friendly
            shutil.copyfile(sample, staged)
            import_photo(
                session,
                focus,
                staged,
                tipo=kind,
                descripcion=description,
                base_dir=ATTACHMENTS,
            )

    # 2. Lista para entregar, con presupuesto y pago.
    ready = reception(
        marta.id,
        kind="Computadora de escritorio",
        brand="Dell",
        model="OptiPlex 7080",
        serial="DLL7080X1",
        problem="Random restarts while working with spreadsheets.",
        days_ago=3,
        priority=Priority.NORMAL,
        diagnosis=Decimal("20"),
        deposit=Decimal("20"),
    )
    add_line(
        session,
        ready,
        tipo=BudgetLineType.REPUESTO,
        descripcion="650 W power supply",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("58"),
    )
    add_line(
        session,
        ready,
        tipo=BudgetLineType.MANO_OBRA,
        descripcion="Power supply replacement and testing",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("25"),
    )
    for state in (
        OrderState.PENDIENTE_DIAGNOSTICO,
        OrderState.DIAGNOSTICADO,
        OrderState.ESPERANDO_APROBACION,
        OrderState.EN_REPARACION,
        OrderState.REPARADO,
        OrderState.LISTO_PARA_ENTREGAR,
    ):
        change_order_state(session, ready, state, USER_ADMIN)
    register_payment(
        session,
        ready,
        tipo=PaymentType.PAGO_FINAL,
        metodo=PaymentMethod.EFECTIVO,
        monto=Decimal("83"),
        usuario=USER_ADMIN,
    )

    # 3. Recién recibida, pendiente de diagnóstico.
    reception(
        carlos.id,
        kind="Impresora",
        brand="Epson",
        model="EcoTank L3250",
        serial="EPSL3250",
        problem="Prints blank pages and the ink levels are not detected.",
        days_ago=0,
        priority=Priority.ALTA,
        diagnosis=Decimal("15"),
    )

    # 4. Diagnosticada, esperando la respuesta del cliente.
    diagnosed = reception(
        luis.id,
        kind="Laptop",
        brand="Lenovo",
        model="ThinkPad T14 Gen 3",
        serial="LNV-T14-7788",
        problem="The keyboard stops responding after a few minutes.",
        days_ago=2,
        priority=Priority.NORMAL,
        diagnosis=Decimal("20"),
    )
    for state in (
        OrderState.PENDIENTE_DIAGNOSTICO,
        OrderState.DIAGNOSTICADO,
        OrderState.ESPERANDO_APROBACION,
    ):
        change_order_state(session, diagnosed, state, USER_TECH)

    # 5. Esperando un repuesto urgente.
    waiting = reception(
        sofia.id,
        kind="Laptop",
        brand="Apple",
        model="MacBook Air M1",
        serial="APL-M1-2020",
        problem="Liquid damage; the trackpad and the battery connector need replacement.",
        days_ago=6,
        priority=Priority.URGENTE,
        diagnosis=Decimal("30"),
    )
    add_line(
        session,
        waiting,
        tipo=BudgetLineType.REPUESTO,
        descripcion="Trackpad assembly",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("95"),
    )
    for state in (
        OrderState.PENDIENTE_DIAGNOSTICO,
        OrderState.DIAGNOSTICADO,
        OrderState.ESPERANDO_APROBACION,
        OrderState.EN_REPARACION,
        OrderState.ESPERANDO_REPUESTO,
    ):
        change_order_state(session, waiting, state, USER_TECH)

    # 6. Entregada y pagada: alimenta el panel de inicio.
    delivered = reception(
        jorge.id,
        kind="Computadora de escritorio",
        brand="Custom",
        model="Ryzen 5 5600",
        serial="CUS-5600-01",
        problem="No video output after moving the computer.",
        days_ago=9,
        priority=Priority.BAJA,
        diagnosis=Decimal("15"),
    )
    add_line(
        session,
        delivered,
        tipo=BudgetLineType.SERVICIO,
        descripcion="Internal cleaning and cable check",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("20"),
    )
    change_order_state(session, delivered, OrderState.EN_REPARACION, USER_ADMIN)
    register_payment(
        session,
        delivered,
        tipo=PaymentType.PAGO_FINAL,
        metodo=PaymentMethod.TARJETA,
        monto=Decimal("35"),
        usuario=USER_ADMIN,
    )
    mark_delivered(session, delivered, usuario=USER_ADMIN)

    # 7. En la papelera, para que la pestaña no salga vacía.
    trashed = reception(
        marta.id,
        kind="Monitor",
        brand="Samsung",
        model="S24R350",
        serial="SAM-S24-350",
        problem="The customer cancelled the service before the diagnosis.",
        days_ago=12,
        priority=Priority.BAJA,
        diagnosis=Decimal("0"),
    )
    soft_delete_order(
        session,
        trashed,
        usuario=USER_ADMIN,
        motivo="Customer cancelled the service.",
    )

    session.commit()
    from luciotech.database.models import User

    admin_row = session.query(User).filter_by(nombre_usuario="ana").one()
    return focus.id, current_user_of(admin_row)


def _shot(widget, name: str, size: tuple[int, int] | None = None) -> None:
    """Muestra el widget, deja pintar a Qt y guarda su área de cliente como PNG."""
    if size is not None:
        widget.setWindowState(Qt.WindowState.WindowNoState)
        widget.resize(*size)
    widget.show()
    QTest.qWait(150)
    QApplication.processEvents()
    pixmap = widget.grab()
    path = OUTPUT / name
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"No se pudo guardar {path}")
    print(f"{path.relative_to(ROOT)}  {pixmap.width()}x{pixmap.height()}")


def _select_contains(combo, text: str) -> None:
    for index in range(combo.count()):
        if text.lower() in combo.itemText(index).lower():
            combo.setCurrentIndex(index)
            return
    raise RuntimeError(f"No se encontró «{text}» en el desplegable")


def _document_png(session: Session, order_id: int, kind: DocumentKind, name: str) -> None:
    """Imprime el documento con el código real y convierte la primera hoja a PNG."""
    from luciotech.database.models import ServiceOrder
    from luciotech.services.settings_service import page_margin_mm, paper_size
    from luciotech.ui.print_support import save_as_pdf
    from PyQt6.QtPrintSupport import QPrinter

    order = session.get(ServiceOrder, order_id)
    if order is None:
        raise RuntimeError("La orden de demostración no existe")
    html = document_html(session, order, kind)
    furniture = _furniture(session, order, kind, USER_ADMIN)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    apply_page_setup(printer, paper_size(session), page_margin_mm(session))
    pdf = WORK / f"{name}.pdf"
    if not save_as_pdf(printer, html, furniture, pdf):
        raise RuntimeError(f"No se pudo escribir {pdf}")
    prefix = WORK / name
    subprocess.run(
        ["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", str(pdf), str(prefix)],
        check=True,
    )
    rendered = next(WORK.glob(f"{name}-*.png"))
    shutil.copyfile(rendered, OUTPUT / name)
    print(f"docs/screenshots/{name}  (desde {pdf.name})")


def main() -> int:
    global WORK, ATTACHMENTS
    WORK = Path(tempfile.mkdtemp(prefix="luciotech-captures-"))
    ATTACHMENTS = WORK / "attachments"
    database = WORK / "demo.sqlite3"
    OUTPUT.mkdir(parents=True, exist_ok=True)

    url = f"sqlite:///{database}"
    upgrade_database(url)
    engine = create_db_engine(url)
    factory: sessionmaker[Session] = create_session_factory(engine)

    # Números y fechas con las convenciones del idioma de la captura (punto decimal).
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    app = QApplication([])
    app.setApplicationName(APP_CONFIG.app_name)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_CONFIG.organization_name)
    # Inglés: no hay catálogo `en`, así que se muestran los literales fuente del código.
    install_translations(app, "en")

    try:
        with factory() as session:
            focus_id, admin = _seed(session)

        # Acceso diario.
        login = LoginDialog(factory)
        _shot(login, "login.png", (460, 300))

        # Ventana principal: inicio, órdenes y papelera.
        window = MainWindow(factory, admin)
        window.setWindowState(Qt.WindowState.WindowNoState)
        window.resize(1280, 760)
        window.show()
        QTest.qWait(250)

        window._tabs.setCurrentIndex(0)
        window.refresh_all()
        QTest.qWait(120)
        _shot(window, "home.png")

        window.resize(1440, 900)
        window._tabs.setCurrentIndex(1)
        window.refresh_all()
        QTest.qWait(120)
        for row in range(window.orders_page.visible_row_count()):
            if window.orders_page.order_number_at(row) == "OT-2026-000001":
                window.orders_page._table.selectRow(row)
                break
        _shot(window, "orders.png")

        window._tabs.setCurrentIndex(4)
        window.refresh_all()
        QTest.qWait(120)
        window.trash_page._table.selectRow(0)
        _shot(window, "trash.png")

        # Recepción: formulario lleno, sin guardar.
        reception = ReceptionDialog(factory, USER_ADMIN)
        reception.setWindowState(Qt.WindowState.WindowNoState)
        reception.resize(1280, 900)
        reception.show()
        QTest.qWait(120)
        _select_contains(reception._customer_combo, "Ana Torres")
        reception._type.setCurrentIndex(reception._type.findData("Laptop"))
        QApplication.processEvents()
        reception._brand.setText("Dell")
        reception._model.setText("Latitude 5420")
        reception._serial.setText("DL5420-9931")
        reception._color.setText("Black")
        reception._os.setText("Windows 11 Pro")
        reception._problem.setPlainText(
            "The screen flickers when the lid is moved and the fan runs constantly."
        )
        reception._physical_state.setPlainText(
            "Hinge loose; small scratch on the lid. Charger and USB-C cable included."
        )
        reception._intake_notes.setPlainText("Customer needs it before Friday.")
        reception._diagnosis_cost.setValue(20)
        reception._deposit.setValue(0)
        for accessory in ("Cargador", "Mouse", "Bolso"):
            checkbox = reception._accessory_checks.get(accessory)
            if checkbox is not None:
                checkbox.setChecked(True)
        reception._manual_accessories.setText("USB-C cable")
        reception._priority.setCurrentIndex(reception._priority.findData(Priority.ALTA.value))
        QTest.qWait(120)
        _shot(reception, "reception.png")

        # Detalle de la orden: las cuatro pestañas del recorrido.
        detail = OrderDetailDialog(factory, focus_id, USER_ADMIN)
        detail.setWindowState(Qt.WindowState.WindowNoState)
        detail.resize(1180, 900)
        detail.show()
        QTest.qWait(250)
        detail._tabs.setCurrentIndex(0)
        QTest.qWait(100)
        _shot(detail, "order-summary.png")

        detail._tabs.setCurrentIndex(1)
        detail._work_tabs.setCurrentIndex(0)
        QTest.qWait(150)
        _shot(detail, "order-work.png")

        detail._work_tabs.setCurrentIndex(3)
        QTest.qWait(250)
        _shot(detail, "order-photos.png")

        detail._tabs.setCurrentIndex(2)
        detail._budget_payments.refresh()
        lines_header = detail._budget_payments._lines.horizontalHeader()
        lines_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        lines_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        lines_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        lines_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        payments_header = detail._budget_payments._payments.horizontalHeader()
        for column in (0, 1, 2, 3, 4):
            payments_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        payments_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        QTest.qWait(150)
        _shot(detail, "order-money.png")

        detail._tabs.setCurrentIndex(3)
        QTest.qWait(120)
        _shot(detail, "order-history.png")

        # Selector de documentos y los dos papeles que más se entregan.
        chooser = DocumentChooserDialog()
        chooser.select(DocumentKind.INFORME)
        _shot(chooser, "documents.png", (620, 400))

        # Configuración: datos del taller y textos legales.
        settings = SettingsDialog(factory)
        settings.resize(900, 720)
        settings.show()
        QTest.qWait(120)
        settings._tabs.setCurrentIndex(0)
        _shot(settings, "settings-workshop.png")
        settings._tabs.setCurrentIndex(2)
        _shot(settings, "settings-terms.png")

        with factory() as session:
            _document_png(session, focus_id, DocumentKind.RECEPCION, "document-reception.png")
            _document_png(session, focus_id, DocumentKind.INFORME, "document-technical-report.png")

        print(f"\n{len(list(OUTPUT.glob('*.png')))} capturas en {OUTPUT.relative_to(ROOT)}")
        return 0
    finally:
        engine.dispose()
        if os.environ.get("LUCIOTECH_KEEP_CAPTURE_WORK"):
            print(f"Archivos de trabajo conservados en {WORK}")
        else:
            shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

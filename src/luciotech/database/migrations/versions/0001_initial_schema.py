"""Esquema inicial: clientes, equipos, órdenes, fotografías, historial, eventos, pagos, configuración y secuencias.

Revision ID: 0001
Revises:
Create Date: 2026-10-09

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre_completo", sa.String(length=200), nullable=False),
        sa.Column("numero_identificacion", sa.String(length=20), nullable=True),
        sa.Column("telefono_principal", sa.String(length=30), nullable=True),
        sa.Column("telefono_secundario", sa.String(length=30), nullable=True),
        sa.Column("correo_electronico", sa.String(length=200), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_numero_identificacion"), "customers", ["numero_identificacion"], unique=False)
    op.create_index(op.f("ix_customers_telefono_principal"), "customers", ["telefono_principal"], unique=False)

    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("tipo_equipo", sa.String(length=60), nullable=False),
        sa.Column("marca", sa.String(length=100), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=True),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("sistema_operativo", sa.String(length=100), nullable=True),
        sa.Column("contrasena_equipo", sa.String(length=200), nullable=True),
        sa.Column("accesorios_recibidos", sa.Text(), nullable=True),
        sa.Column("estado_fisico", sa.Text(), nullable=True),
        sa.Column("problema_reportado_cliente", sa.Text(), nullable=True),
        sa.Column("observaciones_ingreso", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_equipment_cliente_id"), "equipment", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_equipment_numero_serie"), "equipment", ["numero_serie"], unique=False)

    op.create_table(
        "service_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero_orden", sa.String(length=30), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("fecha_ingreso", sa.DateTime(), nullable=False),
        sa.Column("fecha_estimada_entrega", sa.DateTime(), nullable=True),
        sa.Column("fecha_finalizacion", sa.DateTime(), nullable=True),
        sa.Column("fecha_entrega", sa.DateTime(), nullable=True),
        sa.Column("estado", sa.String(length=40), nullable=False),
        sa.Column("prioridad", sa.String(length=20), nullable=False),
        sa.Column("tecnico_responsable", sa.String(length=100), nullable=True),
        sa.Column("problema_reportado", sa.Text(), nullable=True),
        sa.Column("diagnostico_html", sa.Text(), nullable=True),
        sa.Column("trabajo_realizado_html", sa.Text(), nullable=True),
        sa.Column("recomendaciones_html", sa.Text(), nullable=True),
        sa.Column("repuestos_utilizados", sa.Text(), nullable=True),
        sa.Column("costo_diagnostico", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("costo_repuestos", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("costo_mano_obra", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("descuento", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("impuestos", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("anticipo", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("saldo_pendiente", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("garantia_dias", sa.Integer(), nullable=False),
        sa.Column("notas_internas", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("fecha_eliminacion", sa.DateTime(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipment.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_orders_numero_orden"), "service_orders", ["numero_orden"], unique=True)
    op.create_index(op.f("ix_service_orders_cliente_id"), "service_orders", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_service_orders_equipo_id"), "service_orders", ["equipo_id"], unique=False)
    op.create_index(op.f("ix_service_orders_estado"), "service_orders", ["estado"], unique=False)

    op.create_table(
        "photographs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("orden_id", sa.Integer(), nullable=False),
        sa.Column("ruta_archivo", sa.String(length=500), nullable=False),
        sa.Column("nombre_archivo", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("tipo_fotografia", sa.String(length=40), nullable=False),
        sa.Column("fecha_captura", sa.DateTime(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("orden_visualizacion", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["orden_id"], ["service_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_photographs_orden_id"), "photographs", ["orden_id"], unique=False)

    op.create_table(
        "state_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("orden_id", sa.Integer(), nullable=False),
        sa.Column("estado_anterior", sa.String(length=40), nullable=True),
        sa.Column("estado_nuevo", sa.String(length=40), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("usuario", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["orden_id"], ["service_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_state_history_orden_id"), "state_history", ["orden_id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("orden_id", sa.Integer(), nullable=False),
        sa.Column("tipo_evento", sa.String(length=60), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("usuario", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["orden_id"], ["service_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_orden_id"), "events", ["orden_id"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("orden_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("tipo_pago", sa.String(length=40), nullable=False),
        sa.Column("metodo_pago", sa.String(length=40), nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("referencia", sa.String(length=100), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["orden_id"], ["service_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_orden_id"), "payments", ["orden_id"], unique=False)

    op.create_table(
        "configuracion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clave", sa.String(length=100), nullable=False),
        sa.Column("valor", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_configuracion_clave"), "configuracion", ["clave"], unique=True)

    op.create_table(
        "secuencias",
        sa.Column("clave", sa.String(length=50), nullable=False),
        sa.Column("ultimo_valor", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("clave"),
    )


def downgrade() -> None:
    op.drop_table("secuencias")
    op.drop_index(op.f("ix_configuracion_clave"), table_name="configuracion")
    op.drop_table("configuracion")
    op.drop_index(op.f("ix_payments_orden_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_events_orden_id"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_state_history_orden_id"), table_name="state_history")
    op.drop_table("state_history")
    op.drop_index(op.f("ix_photographs_orden_id"), table_name="photographs")
    op.drop_table("photographs")
    op.drop_index(op.f("ix_service_orders_estado"), table_name="service_orders")
    op.drop_index(op.f("ix_service_orders_equipo_id"), table_name="service_orders")
    op.drop_index(op.f("ix_service_orders_cliente_id"), table_name="service_orders")
    op.drop_index(op.f("ix_service_orders_numero_orden"), table_name="service_orders")
    op.drop_table("service_orders")
    op.drop_index(op.f("ix_equipment_numero_serie"), table_name="equipment")
    op.drop_index(op.f("ix_equipment_cliente_id"), table_name="equipment")
    op.drop_table("equipment")
    op.drop_index(op.f("ix_customers_telefono_principal"), table_name="customers")
    op.drop_index(op.f("ix_customers_numero_identificacion"), table_name="customers")
    op.drop_table("customers")

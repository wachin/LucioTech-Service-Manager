"""Bitácora de cuentas y contraseña temporal obligatoria (§19).

Cada cuenta puede quedar marcada para cambiar la contraseña en el siguiente acceso: es lo
que pasa cuando un administrador restablece la de otra persona, porque la contraseña nueva
solo la conoce él. Además, toda alta, cambio de rol, activación, desactivación y cambio de
contraseña deja un renglón en `eventos_usuario`, con quién lo hizo y a quién.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-24

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Las cuentas que ya existen siguen entrando con su contraseña actual.
    op.add_column(
        "usuarios",
        sa.Column(
            "debe_cambiar_contrasena",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_table(
        "eventos_usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("usuario_nombre", sa.String(length=120), nullable=False),
        sa.Column("afectado_id", sa.Integer(), nullable=False),
        sa.Column("afectado_nombre", sa.String(length=120), nullable=False),
        sa.Column("accion", sa.String(length=40), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["afectado_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eventos_usuario_fecha", "eventos_usuario", ["fecha"])


def downgrade() -> None:
    op.drop_index("ix_eventos_usuario_fecha", table_name="eventos_usuario")
    op.drop_table("eventos_usuario")
    op.drop_column("usuarios", "debe_cambiar_contrasena")

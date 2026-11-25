"""Usuarios, contraseñas y sesión de la aplicación (§19).

Un usuario tiene un **nombre de acceso** (`nombre_usuario`, en minúsculas y sin espacios, el
que se teclea al entrar) y un **nombre completo** (`nombre_completo`, el que se ve en la barra
de la ventana, en el historial de las órdenes y en el pie de los documentos que imprime).

La contraseña nunca se guarda en claro ni se registra en ningún log: se guarda el hash PBKDF2
con su sal, y la comparación es de tiempo constante. Todo con la biblioteca estándar, sin
dependencias nuevas.

Los servicios reciben la sesión y hacen `flush`, no `commit`; el commit lo pone la interfaz,
igual que en el resto del proyecto.

Toda alta, cambio de rol o de nombre, activación, desactivación y cambio de contraseña deja
un renglón en la bitácora `eventos_usuario` con quién lo hizo y a quién. La contraseña que
restablece un administrador queda marcada como temporal (`debe_cambiar_contrasena`) para que
la persona afectada tenga que poner una propia en el siguiente acceso.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import QCoreApplication
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from luciotech.config import DEFAULT_USER
from luciotech.database.enums import UserAuditAction, UserRole
from luciotech.database.models import User, UserEvent

HASH_ALGORITHM = "sha256"
HASH_ITERATIONS = 260_000
HASH_PREFIX = "pbkdf2_sha256"
SALT_BYTES = 16

MIN_PASSWORD_LENGTH = 4
MAX_PASSWORD_LENGTH = 200
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 60

_USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]+$")


@dataclass(frozen=True)
class CurrentUser:
    """Quién tiene la sesión abierta, tal como lo necesitan la interfaz y los documentos."""

    id: int | None
    username: str
    full_name: str
    role: str = UserRole.TECNICO.value

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMINISTRADOR.value

    @property
    def display_name(self) -> str:
        """Nombre que se escribe en el historial y en los documentos."""
        return self.full_name.strip() or self.username


# Usuario por defecto para las pruebas y para cualquier código que todavía no reciba la sesión
# iniciada: es el nombre que usaba la aplicación antes de tener cuentas.
DEFAULT_CURRENT_USER = CurrentUser(
    id=None, username="", full_name=DEFAULT_USER, role=UserRole.ADMINISTRADOR.value
)


def normalize_username(username: str) -> str:
    """Los nombres de acceso se guardan y se buscan en minúsculas, sin espacios alrededor."""
    return username.strip().lower()


def hash_password(password: str) -> str:
    """Devuelve `pbkdf2_sha256$iteraciones$sal$hash`, que es lo único que se guarda."""
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM, password.encode("utf-8"), salt.encode("ascii"), HASH_ITERATIONS
    )
    return f"{HASH_PREFIX}${HASH_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Compara una contraseña con el hash guardado; nunca lanza excepción."""
    if not stored:
        return False
    try:
        prefix, iterations, salt, expected = stored.split("$")
        rounds = int(iterations)
    except ValueError:
        return False
    if prefix != HASH_PREFIX or rounds <= 0:
        return False
    digest = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM, password.encode("utf-8"), salt.encode("ascii"), rounds
    )
    return hmac.compare_digest(digest.hex(), expected)


def validate_username(username: str) -> str:
    """Normaliza y valida el nombre de acceso; devuelve el valor que se guarda."""
    value = normalize_username(username)
    if len(value) < MIN_USERNAME_LENGTH:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "The user name must have at least {count} characters."
            ).format(count=MIN_USERNAME_LENGTH)
        )
    if len(value) > MAX_USERNAME_LENGTH:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "The user name cannot be longer than {count} characters."
            ).format(count=MAX_USERNAME_LENGTH)
        )
    if not _USERNAME_PATTERN.match(value):
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech",
                "The user name may only contain unaccented letters, digits, dot, hyphen "
                "and underscore.",
            )
        )
    return value


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "The password must have at least {count} characters."
            ).format(count=MIN_PASSWORD_LENGTH)
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "The password cannot be longer than {count} characters."
            ).format(count=MAX_PASSWORD_LENGTH)
        )


def validate_full_name(full_name: str) -> str:
    value = " ".join(full_name.split())
    if not value:
        raise ValueError(
            QCoreApplication.translate("LucioTech", "The full name cannot be empty.")
        )
    if len(value) > 120:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "The full name cannot be longer than 120 characters."
            )
        )
    return value


def count_users(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(User)) or 0)


def has_users(session: Session) -> bool:
    return count_users(session) > 0


def list_users(session: Session, *, only_active: bool = False) -> list[User]:
    query = select(User)
    if only_active:
        query = query.where(User.activo.is_(True))
    return list(session.scalars(query.order_by(User.activo.desc(), User.nombre_completo)))


def record_user_event(
    session: Session,
    *,
    actor: CurrentUser | None,
    affected: User,
    action: UserAuditAction | str,
    detail: str | None = None,
) -> UserEvent:
    """Anota en la bitácora de cuentas quién hizo qué y a quién (sin commit)."""
    event = UserEvent(
        usuario_id=actor.id if actor is not None else None,
        usuario_nombre=actor.display_name if actor is not None else "",
        afectado_id=affected.id,
        afectado_nombre=affected.nombre_completo,
        accion=UserAuditAction(action).value,
        detalle=detail,
    )
    session.add(event)
    session.flush()
    return event


def list_user_events(session: Session, *, limit: int = 200) -> list[UserEvent]:
    """Últimos movimientos de cuentas, del más nuevo al más viejo."""
    return list(
        session.scalars(
            select(UserEvent)
            .order_by(UserEvent.fecha.desc(), UserEvent.id.desc())
            .limit(limit)
        )
    )


def list_login_users(session: Session) -> list[User]:
    """Cuentas activas para la lista de acceso, en el orden del último acceso.

    Las cuentas que ya han entrado alguna vez van primero, porque suele ser la misma
    persona la que abre el taller cada día; las que todavía no han accedido (ultimo_acceso
    nulo) quedan al final.
    """
    return list(
        session.scalars(
            select(User)
            .where(User.activo.is_(True))
            .order_by(User.ultimo_acceso.desc(), User.nombre_completo)
        )
    )


def get_user(session: Session, username: str) -> User | None:
    return session.scalar(
        select(User).where(User.nombre_usuario == normalize_username(username))
    )


def create_user(
    session: Session,
    *,
    username: str,
    full_name: str,
    password: str,
    role: UserRole | str = UserRole.TECNICO,
    actor: CurrentUser | None = None,
) -> User:
    """Crea un usuario y lo deja en la sesión (sin commit).

    Valida el nombre de acceso, el nombre completo y la contraseña, y rechaza los nombres de
    acceso repetidos sin importar cómo se escriban. `actor` es quien da el alta, para la
    bitácora; el alta que se hace desde el acceso no tiene nadie con quien firmarla.
    """
    value = validate_username(username)
    name = validate_full_name(full_name)
    validate_password(password)
    role_value = UserRole(role).value
    if get_user(session, value) is not None:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "A user with that sign-in name already exists."
            )
        )
    user = User(
        nombre_usuario=value,
        nombre_completo=name,
        contrasena_hash=hash_password(password),
        rol=role_value,
        activo=True,
        debe_cambiar_contrasena=False,
    )
    session.add(user)
    session.flush()
    record_user_event(
        session, actor=actor, affected=user, action=UserAuditAction.ALTA, detail=role_value
    )
    return user


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Devuelve el usuario si la contraseña es correcta y la cuenta está activa.

    Cuando el usuario no existe se gasta el mismo tiempo en calcular un hash, para que el
    tiempo de respuesta no delate qué nombres de acceso existen.
    """
    user = get_user(session, username)
    if user is None:
        hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            b"luciotech-usuario-inexistente",
            HASH_ITERATIONS,
        )
        return None
    if not verify_password(password, user.contrasena_hash):
        return None
    if not user.activo:
        return None
    return user


def touch_login(session: Session, user: User) -> None:
    """Anota la fecha del último acceso correcto."""
    user.ultimo_acceso = datetime.now()
    session.flush()


def current_user_of(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        username=user.nombre_usuario,
        full_name=user.nombre_completo,
        role=user.rol,
    )


def _store_password(session: Session, user: User, password: str, *, must_change: bool) -> None:
    validate_password(password)
    user.contrasena_hash = hash_password(password)
    user.debe_cambiar_contrasena = must_change
    session.flush()


def _confirm_other_admin_reset(
    session: Session,
    user: User,
    *,
    actor: CurrentUser | None,
    actor_password: str | None,
) -> None:
    """Exige la contraseña de quien administra para tocar la de otro administrador.

    Restablecer la contraseña de un técnico no da acceso a nada más; la de otro
    administrador sí, así que no basta con tener la sesión abierta: hay que demostrar que
    quien está sentado delante es de verdad el dueño de esa sesión.
    """
    if (
        actor is None
        or actor.id is None
        or actor.id == user.id
        or user.rol != UserRole.ADMINISTRADOR.value
    ):
        return
    if not actor_password:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech",
                "Enter your own password to reset another administrator's password.",
            )
        )
    actor_user = session.get(User, actor.id)
    if actor_user is None or not verify_password(
        actor_password, actor_user.contrasena_hash
    ):
        raise ValueError(
            QCoreApplication.translate("LucioTech", "Your password is not correct.")
        )


def set_password(
    session: Session,
    user: User,
    password: str,
    *,
    actor: CurrentUser | None = None,
    actor_password: str | None = None,
) -> None:
    """Restablece la contraseña de otra cuenta, sin pedir la anterior.

    Queda marcada como temporal: solo la conoce quien la escribió, así que la persona tendrá
    que elegir una propia en su siguiente acceso. Si la cuenta es la de otro administrador,
    `actor_password` tiene que traer la contraseña de `actor`; el cambio se anota en la
    bitácora con el nombre de quien lo hizo.
    """
    _confirm_other_admin_reset(
        session, user, actor=actor, actor_password=actor_password
    )
    _store_password(session, user, password, must_change=True)
    record_user_event(
        session,
        actor=actor,
        affected=user,
        action=UserAuditAction.CONTRASENA_RESTABLECIDA,
    )


def change_own_password(session: Session, user: User, current: str, new: str) -> None:
    """Cambio de contraseña por el propio usuario: exige la contraseña actual."""
    if not verify_password(current, user.contrasena_hash):
        raise ValueError(
            QCoreApplication.translate("LucioTech", "The current password is not correct.")
        )
    _store_password(session, user, new, must_change=False)
    record_user_event(
        session,
        actor=current_user_of(user),
        affected=user,
        action=UserAuditAction.CONTRASENA_PROPIA,
    )


def update_user(
    session: Session,
    user: User,
    *,
    full_name: str | None = None,
    role: UserRole | str | None = None,
    actor: CurrentUser | None = None,
    actor_password: str | None = None,
) -> None:
    """Cambia el nombre visible o el rol, sin dejar el sistema sin administradores.

    Degradar a otro administrador a técnico exige la contraseña de quien lo hace, igual
    que al desactivarlo o al restablecerle la contraseña: la sesión abierta no basta.
    """
    if full_name is not None:
        name = validate_full_name(full_name)
        if name != user.nombre_completo:
            user.nombre_completo = name
            record_user_event(
                session,
                actor=actor,
                affected=user,
                action=UserAuditAction.EDICION,
                detail=name,
            )
    if role is not None:
        new_role = UserRole(role).value
        if new_role != user.rol:
            if user.rol == UserRole.ADMINISTRADOR.value:
                _ensure_another_admin(session, user)
                if (
                    new_role != UserRole.ADMINISTRADOR.value
                    and actor is not None
                    and actor.id is not None
                    and actor.id != user.id
                    and user.activo
                ):
                    if not actor_password:
                        raise ValueError(
                            QCoreApplication.translate(
                                "LucioTech",
                                "Enter your own password to reset another administrator's password.",
                            )
                        )
                    actor_user = session.get(User, actor.id)
                    if actor_user is None or not verify_password(
                        actor_password, actor_user.contrasena_hash
                    ):
                        raise ValueError(
                            QCoreApplication.translate(
                                "LucioTech", "Your password is not correct."
                            )
                        )
            previous = user.rol
            user.rol = new_role
            record_user_event(
                session,
                actor=actor,
                affected=user,
                action=UserAuditAction.ROL,
                detail=f"{previous} → {new_role}",
            )
    session.flush()


def set_active(
    session: Session,
    user: User,
    active: bool,
    *,
    actor: CurrentUser | None = None,
    actor_password: str | None = None,
) -> None:
    """Activa o desactiva una cuenta; la última cuenta de administrador no se puede apagar.

    Desactivar a otro administrador exige la contraseña de quien lo hace.
    """
    if not active:
        _ensure_another_admin(session, user)
        if (
            actor is not None
            and actor.id is not None
            and actor.id != user.id
            and user.rol == UserRole.ADMINISTRADOR.value
            and user.activo
        ):
            if not actor_password:
                raise ValueError(
                    QCoreApplication.translate(
                        "LucioTech",
                        "Enter your own password to reset another administrator's password.",
                    )
                )
            actor_user = session.get(User, actor.id)
            if actor_user is None or not verify_password(
                actor_password, actor_user.contrasena_hash
            ):
                raise ValueError(
                    QCoreApplication.translate(
                        "LucioTech", "Your password is not correct."
                    )
                )
    user.activo = active
    session.flush()
    record_user_event(
        session,
        actor=actor,
        affected=user,
        action=UserAuditAction.ACTIVADO if active else UserAuditAction.DESACTIVADO,
    )


def _ensure_another_admin(session: Session, user: User) -> None:
    if user.rol != UserRole.ADMINISTRADOR.value:
        return
    others = session.scalar(
        select(func.count())
        .select_from(User)
        .where(
            User.rol == UserRole.ADMINISTRADOR.value,
            User.activo.is_(True),
            User.id != user.id,
        )
    )
    if not others:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "At least one active administrator must remain."
            )
        )


def create_first_admin(session: Session, *, username: str, full_name: str, password: str) -> User:
    """Crea la cuenta de administrador de un equipo que todavía no tiene ninguna."""
    if has_users(session):
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "Users have already been created on this computer."
            )
        )
    return create_user(
        session,
        username=username,
        full_name=full_name,
        password=password,
        role=UserRole.ADMINISTRADOR,
    )

"""Repositorios: acceso CRUD a las entidades a través de la sesión SQLAlchemy.

Los repositorios solo hacen flush; el límite de la transacción lo decide quien los usa.
"""

from __future__ import annotations

from typing import Any, ClassVar, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from luciotech.database.models import Base, Customer, Equipment, ServiceOrder

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    model: ClassVar[type[Any]]

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: T) -> T:
        self._session.add(entity)
        self._session.flush()
        return entity

    def get(self, entity_id: int) -> T | None:
        return self._session.get(self.model, entity_id)

    def save(self, entity: T) -> T:
        self._session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self._session.delete(entity)
        self._session.flush()


class CustomerRepository(Repository[Customer]):
    model = Customer

    def list_all(self) -> list[Customer]:
        statement = select(Customer).order_by(Customer.nombre_completo)
        return list(self._session.scalars(statement))


class EquipmentRepository(Repository[Equipment]):
    model = Equipment


class ServiceOrderRepository(Repository[ServiceOrder]):
    model = ServiceOrder

    def get_by_number(self, numero_orden: str) -> ServiceOrder | None:
        statement = select(ServiceOrder).where(ServiceOrder.numero_orden == numero_orden)
        return self._session.scalar(statement)

    def list_active(self) -> list[ServiceOrder]:
        statement = (
            select(ServiceOrder)
            .where(ServiceOrder.activo.is_(True))
            .order_by(ServiceOrder.fecha_ingreso.desc())
        )
        return list(self._session.scalars(statement))

    def list_deleted(self) -> list[ServiceOrder]:
        statement = (
            select(ServiceOrder)
            .where(ServiceOrder.activo.is_(False))
            .order_by(ServiceOrder.fecha_eliminacion.desc())
        )
        return list(self._session.scalars(statement))

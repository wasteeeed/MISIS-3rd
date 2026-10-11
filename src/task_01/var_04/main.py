# Сервис проката

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models import Rental, ReturnInfo, Transport, User
from validate import (
    validate_found,
    validate_registered,
    validate_text,
    validate_type,
    validate_unique_ids,
)


@dataclass(frozen=True, slots=True)
class RentalService:
    transports: tuple[Transport, ...]

    def __post_init__(self) -> None:
        transports = tuple(self.transports)
        for transport in transports:
            validate_type(transport, Transport, "transport")
        validate_unique_ids(tuple(transport.transport_id for transport in transports))
        object.__setattr__(self, "transports", transports)

    def rent(self, transport_id: str, user: User, starts_at: datetime) -> Rental:
        validate_text(transport_id, "transport_id")
        transport = validate_found(
            next(
                (item for item in self.transports if item.transport_id == transport_id),
                None,
            ),
            "Транспорт не найден в каталоге",
        )
        return transport.rent(user, starts_at)

    def finish_rental(
        self, rental: Rental, ends_at: datetime, info: ReturnInfo
    ) -> Decimal:
        validate_type(rental, Rental, "rental")
        validate_registered(
            any(transport is rental.transport for transport in self.transports),
            "Транспорт не зарегистрирован в сервисе",
        )
        return rental.transport.return_back(rental, ends_at, info)

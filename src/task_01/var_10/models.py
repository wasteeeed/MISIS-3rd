# Модели и операции

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from validate import (
    validate_active_reservation,
    validate_available_quantity,
    validate_move_zones,
    validate_positive_quantity,
    validate_reservation,
    validate_stock_values,
    validate_text,
)

DEFAULT_ZONE = "MAIN"


# Снимок остатков
@dataclass(frozen=True, slots=True)
class Stock:
    total: int
    reserved: int

    def __post_init__(self) -> None:
        validate_stock_values(self.total, self.reserved)

    @property
    def available(self) -> int:
        return self.total - self.reserved


# Рабочее состояние
@dataclass(slots=True)
class StockState:
    zone_totals: dict[tuple[str, str], int] = field(default_factory=dict)
    reservations: dict[tuple[str, str], tuple[tuple[str, int], ...]] = field(
        default_factory=dict
    )

    def stock(self, product_id: str, zone_id: str | None = None) -> Stock:
        total = sum(
            quantity
            for (product, zone), quantity in self.zone_totals.items()
            if product == product_id and (zone_id is None or zone == zone_id)
        )
        reserved = sum(
            quantity
            for (product, _), allocations in self.reservations.items()
            if product == product_id
            for zone, quantity in allocations
            if zone_id is None or zone == zone_id
        )
        return Stock(total, reserved)

    def close_reservation(
        self, product_id: str, order_id: str
    ) -> tuple[tuple[str, int], ...]:
        validate_text(order_id, "order_id")
        key = (product_id, order_id)
        validate_active_reservation(key in self.reservations)
        return self.reservations.pop(key)


# Абстрактная операция
@dataclass(frozen=True, kw_only=True)
class StockOperation(ABC):
    product_id: str
    reason: str

    @abstractmethod
    def apply(self, state: StockState) -> None:
        pass


@dataclass(frozen=True, kw_only=True)
class ReceiptOperation(StockOperation):
    quantity: int
    zone_id: str = DEFAULT_ZONE

    def apply(self, state: StockState) -> None:
        validate_positive_quantity(self.quantity)
        validate_text(self.zone_id, "zone_id")
        key = (self.product_id, self.zone_id)
        state.zone_totals[key] = state.zone_totals.get(key, 0) + self.quantity


@dataclass(frozen=True, kw_only=True)
class ReserveOperation(StockOperation):
    order_id: str
    quantity: int

    def apply(self, state: StockState) -> None:
        validate_text(self.order_id, "order_id")
        key = (self.product_id, self.order_id)
        validate_reservation(
            self.quantity,
            state.stock(self.product_id).available,
            key in state.reservations,
        )

        remaining = self.quantity
        allocations: list[tuple[str, int]] = []
        for product_id, zone_id in state.zone_totals:
            if product_id != self.product_id:
                continue
            available = state.stock(product_id, zone_id).available
            if available <= 0:
                continue
            quantity = min(remaining, available)
            allocations.append((zone_id, quantity))
            remaining -= quantity
            if remaining == 0:
                break
        state.reservations[key] = tuple(allocations)


@dataclass(frozen=True, kw_only=True)
class ConfirmReservationOperation(StockOperation):
    order_id: str

    def apply(self, state: StockState) -> None:
        for zone_id, quantity in state.close_reservation(
            self.product_id, self.order_id
        ):
            state.zone_totals[(self.product_id, zone_id)] -= quantity


@dataclass(frozen=True, kw_only=True)
class CancelReservationOperation(StockOperation):
    order_id: str

    def apply(self, state: StockState) -> None:
        state.close_reservation(self.product_id, self.order_id)


@dataclass(frozen=True, kw_only=True)
class MoveOperation(StockOperation):
    from_zone_id: str
    to_zone_id: str
    quantity: int

    def apply(self, state: StockState) -> None:
        validate_move_zones(self.from_zone_id, self.to_zone_id)
        validate_available_quantity(
            self.quantity,
            state.stock(self.product_id, self.from_zone_id).available,
            "Недостаточно доступного товара в исходной зоне",
        )
        source = (self.product_id, self.from_zone_id)
        destination = (self.product_id, self.to_zone_id)
        state.zone_totals[source] -= self.quantity
        state.zone_totals[destination] = (
            state.zone_totals.get(destination, 0) + self.quantity
        )


@dataclass(frozen=True, kw_only=True)
class WriteOffOperation(StockOperation):
    quantity: int
    zone_id: str = DEFAULT_ZONE

    def apply(self, state: StockState) -> None:
        validate_text(self.zone_id, "zone_id")
        validate_available_quantity(
            self.quantity,
            state.stock(self.product_id, self.zone_id).available,
            "Недостаточно доступного товара для списания",
        )
        state.zone_totals[(self.product_id, self.zone_id)] -= self.quantity

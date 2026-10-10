# Модели и правила

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from validate import (
    validate_boolean,
    validate_discount_amount,
    validate_found,
    validate_money,
    validate_optional_text,
    validate_order_editable,
    validate_order_items,
    validate_percentage,
    validate_positive_int,
    validate_text,
    validate_type,
)

ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    name: str
    price: Decimal
    available: bool = True

    def __post_init__(self) -> None:
        validate_text(self.product_id, "product_id")
        validate_text(self.name, "name")
        validate_money(self.price, "price")
        validate_boolean(self.available, "available")


@dataclass(frozen=True, slots=True)
class OrderItem:
    product: Product
    quantity: int

    def __post_init__(self) -> None:
        validate_type(self.product, Product, "product")
        validate_positive_int(self.quantity, "quantity")

    @property
    def subtotal(self) -> Decimal:
        return self.product.price * self.quantity


@dataclass(frozen=True, slots=True)
class DeliveryOption:
    name: str
    cost: Decimal = ZERO

    def __post_init__(self) -> None:
        validate_text(self.name, "name")
        validate_money(self.cost, "delivery_cost", allow_zero=True)


def _percentage_discount(subtotal: Decimal, percent: Decimal) -> Decimal:
    return subtotal * percent / Decimal(100)


class DiscountRule(ABC):
    @abstractmethod
    def calculate(
        self, subtotal: Decimal, quantity: int, promo_code: str | None
    ) -> Decimal:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class AmountDiscount(DiscountRule):
    minimum_amount: Decimal
    percent: Decimal

    def __post_init__(self) -> None:
        validate_money(self.minimum_amount, "minimum_amount")
        validate_percentage(self.percent)

    def calculate(
        self, subtotal: Decimal, quantity: int, promo_code: str | None
    ) -> Decimal:
        if subtotal >= self.minimum_amount:
            return _percentage_discount(subtotal, self.percent)
        return ZERO


@dataclass(frozen=True, slots=True)
class PromoCodeDiscount(DiscountRule):
    code: str
    percent: Decimal

    def __post_init__(self) -> None:
        validate_text(self.code, "code")
        validate_percentage(self.percent)

    def calculate(
        self, subtotal: Decimal, quantity: int, promo_code: str | None
    ) -> Decimal:
        if promo_code == self.code:
            return _percentage_discount(subtotal, self.percent)
        return ZERO


@dataclass(frozen=True, slots=True)
class QuantityDiscount(DiscountRule):
    minimum_quantity: int
    percent: Decimal

    def __post_init__(self) -> None:
        validate_positive_int(self.minimum_quantity, "minimum_quantity")
        validate_percentage(self.percent)

    def calculate(
        self, subtotal: Decimal, quantity: int, promo_code: str | None
    ) -> Decimal:
        if quantity >= self.minimum_quantity:
            return _percentage_discount(subtotal, self.percent)
        return ZERO


class OrderStatus(Enum):
    CREATED = "created"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderState(ABC):
    status: ClassVar[OrderStatus]
    editable: ClassVar[bool] = False

    @abstractmethod
    def transitions(self) -> dict[str, type[OrderState]]:
        raise NotImplementedError

    def next_state(self, action: str) -> OrderState:
        state_type = validate_found(
            self.transitions().get(action),
            f"Действие {action} запрещено в состоянии {self.status.value}",
        )
        return state_type()


class CreatedState(OrderState):
    status = OrderStatus.CREATED
    editable = True

    def transitions(self) -> dict[str, type[OrderState]]:
        return {"submit": AwaitingPaymentState, "cancel": CancelledState}


class AwaitingPaymentState(OrderState):
    status = OrderStatus.AWAITING_PAYMENT

    def transitions(self) -> dict[str, type[OrderState]]:
        return {"pay": PaidState, "cancel": CancelledState}


class PaidState(OrderState):
    status = OrderStatus.PAID

    def transitions(self) -> dict[str, type[OrderState]]:
        return {"ship": ShippedState}


class ShippedState(OrderState):
    status = OrderStatus.SHIPPED

    def transitions(self) -> dict[str, type[OrderState]]:
        return {"complete": CompletedState}


class CompletedState(OrderState):
    status = OrderStatus.COMPLETED

    def transitions(self) -> dict[str, type[OrderState]]:
        return {}


class CancelledState(OrderState):
    status = OrderStatus.CANCELLED

    def transitions(self) -> dict[str, type[OrderState]]:
        return {}


@dataclass(frozen=True, slots=True, eq=False)
class Order:
    items: tuple[OrderItem, ...]
    delivery: DeliveryOption
    promo_code: str | None = None
    discount: Decimal = field(default=ZERO, init=False)
    __state: OrderState = field(default_factory=CreatedState, init=False, repr=False)

    def __post_init__(self) -> None:
        items = tuple(self.items)
        for item in items:
            validate_type(item, OrderItem, "item")
        validate_order_items(bool(items), all(item.product.available for item in items))
        validate_type(self.delivery, DeliveryOption, "delivery")
        validate_optional_text(self.promo_code, "promo_code")
        object.__setattr__(self, "items", items)

    @property
    def status(self) -> OrderStatus:
        return self.__state.status

    @property
    def quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self) -> Decimal:
        return sum((item.subtotal for item in self.items), ZERO)

    @property
    def total(self) -> Decimal:
        return self.subtotal - self.discount + self.delivery.cost

    def submit(self) -> None:
        self._transition("submit")

    def pay(self) -> None:
        self._transition("pay")

    def ship(self) -> None:
        self._transition("ship")

    def complete(self) -> None:
        self._transition("complete")

    def cancel(self) -> None:
        self._transition("cancel")

    def _transition(self, action: str) -> None:
        updated = self.__state.next_state(action)
        object.__setattr__(self, "_Order__state", updated)

    def _ensure_editable(self) -> None:
        validate_order_editable(self.__state.editable)

    def _set_discount(self, amount: Decimal) -> None:
        self._ensure_editable()
        validate_discount_amount(amount, self.subtotal)
        validate_money(amount, "discount", allow_zero=True)
        object.__setattr__(self, "discount", amount)

    def _replace_contents(self, candidate: Order) -> None:
        self._ensure_editable()
        validate_type(candidate, Order, "candidate")
        object.__setattr__(self, "items", candidate.items)
        object.__setattr__(self, "delivery", candidate.delivery)
        object.__setattr__(self, "promo_code", candidate.promo_code)
        object.__setattr__(self, "discount", candidate.discount)

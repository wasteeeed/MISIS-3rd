# Валидация

from decimal import Decimal, InvalidOperation
from typing import TypeVar

CENT = Decimal("0.01")
T = TypeVar("T")


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


def validate_optional_text(value: str | None, name: str) -> None:
    if value is not None:
        validate_text(value, name)


def validate_type(value: object, expected_type: type, name: str) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Некорректный тип: {name}")


def validate_positive_int(value: int, name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} должен быть положительным целым числом")


def validate_boolean(value: bool, name: str) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} должен быть логическим значением")


def validate_money(value: Decimal, name: str, allow_zero: bool = False) -> None:
    validate_type(value, Decimal, name)
    if not value.is_finite() or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f"Некорректная денежная сумма: {name}")
    try:
        rounded = value.quantize(CENT)
    except InvalidOperation as error:
        raise ValueError(f"Некорректная денежная сумма: {name}") from error
    if value != rounded:
        raise ValueError(f"{name} должен содержать не более двух знаков после запятой")


def validate_percentage(value: Decimal) -> None:
    validate_type(value, Decimal, "percent")
    if not value.is_finite() or not 0 < value <= 100:
        raise ValueError("Процент должен быть больше 0 и не больше 100")


def validate_discount_amount(value: Decimal, subtotal: Decimal) -> None:
    validate_type(value, Decimal, "discount")
    if not value.is_finite() or not 0 <= value <= subtotal:
        raise ValueError("Скидка должна находиться между нулём и суммой товаров")


def validate_order_items(nonempty: bool, available: bool) -> None:
    if not nonempty:
        raise ValueError("Нельзя оформить заказ из пустой корзины")
    if not available:
        raise ValueError("В заказе есть недоступный товар")


def validate_same_product(matches: bool) -> None:
    if not matches:
        raise ValueError("Один идентификатор не может обозначать разные товары")


def validate_order_editable(allowed: bool) -> None:
    if not allowed:
        raise ValueError("Заказ можно изменять только в состоянии created")


def validate_found(value: T | None, message: str) -> T:
    if value is None:
        raise ValueError(message)
    return value

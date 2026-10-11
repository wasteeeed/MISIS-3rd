# Валидация

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import TypeVar

CENT = Decimal("0.01")
T = TypeVar("T")


def validate_type(value: object, expected_type: type, name: str) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Некорректный тип: {name}")


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


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


def validate_datetime(value: datetime, name: str) -> None:
    validate_type(value, datetime, name)
    if value.tzinfo is not None:
        raise ValueError("Укажите местное время пункта проката без часового пояса")


def validate_time_range(starts_at: datetime, ends_at: datetime) -> None:
    validate_datetime(starts_at, "starts_at")
    validate_datetime(ends_at, "ends_at")
    if ends_at <= starts_at:
        raise ValueError("Время окончания должно быть позже времени начала")


def validate_duration(value: timedelta) -> None:
    validate_type(value, timedelta, "duration")
    if value <= timedelta(0):
        raise ValueError("Продолжительность аренды должна быть положительной")


def validate_optional_percent(value: int | None, name: str) -> None:
    if value is not None and (type(value) is not int or not 0 <= value <= 100):
        raise ValueError(f"{name} должен быть целым числом от 0 до 100")


def validate_available(available: bool) -> None:
    if not available:
        raise ValueError("Транспорт уже арендован")


def validate_minimum_age(age: int, minimum: int) -> None:
    if age < minimum:
        raise ValueError(f"Для аренды нужен возраст от {minimum} лет")


def validate_license(has_license: bool) -> None:
    if not has_license:
        raise ValueError("Для аренды автомобиля нужны водительские права")


def validate_return_level(value: int | None, minimum: int, name: str) -> None:
    if value is None:
        raise ValueError(f"Укажите {name} при возврате")
    if value < minimum:
        raise ValueError(f"При возврате {name} должен быть не ниже {minimum}%")


def validate_unique_ids(transport_ids: tuple[str, ...]) -> None:
    if len(transport_ids) != len(set(transport_ids)):
        raise ValueError("Идентификаторы транспорта должны различаться")


def validate_registered(registered: bool, message: str) -> None:
    if not registered:
        raise ValueError(message)


def validate_found(value: T | None, message: str) -> T:
    if value is None:
        raise ValueError(message)
    return value

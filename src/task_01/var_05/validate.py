# Валидация

from datetime import date
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def validate_type(value: object, expected_type: type, name: str) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Некорректный тип: {name}")


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


def validate_month(value: date) -> None:
    if type(value) is not date:
        raise TypeError("month должен быть датой")
    if value.day != 1:
        raise ValueError("month должен указывать на первое число месяца")


def validate_decimal(value: Decimal, name: str, allow_zero: bool = False) -> None:
    validate_type(value, Decimal, name)
    if not value.is_finite() or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f"Некорректное значение: {name}")


def validate_money(value: Decimal, name: str, allow_zero: bool = False) -> None:
    validate_decimal(value, name, allow_zero)
    try:
        rounded = value.quantize(CENT)
    except InvalidOperation as error:
        raise ValueError(f"Некорректная денежная сумма: {name}") from error
    if value != rounded:
        raise ValueError(f"{name} должен содержать не более двух знаков после запятой")


def validate_registration(
    employee_month: date, department_month: date, already_registered: bool
) -> None:
    if employee_month != department_month:
        raise ValueError("Месяц сотрудника не совпадает с месяцем подразделения")
    if already_registered:
        raise ValueError("Сотрудник с таким идентификатором уже добавлен")

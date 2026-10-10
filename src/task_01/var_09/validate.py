# Валидация

from typing import TypeVar

T = TypeVar("T")


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


def validate_positive_int(value: int, name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} должен быть положительным целым числом")


def validate_boolean(value: bool, name: str) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} должен быть логическим значением")


def validate_type(value: object, expected_type: type, name: str) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Некорректный тип: {name}")


def validate_specializations(values: frozenset[str]) -> None:
    if not isinstance(values, (set, frozenset)) or not values:
        raise ValueError("Нужна хотя бы одна специализация")
    for value in values:
        validate_text(value, "specialization")


def validate_transition(current: str, expected: str, target: str) -> None:
    if current != expected:
        raise ValueError(f"Переход {current} -> {target} запрещён")


def validate_assignee(exists: bool) -> None:
    if not exists:
        raise ValueError("Сначала нужно назначить исполнителя")


def validate_assignment_allowed(allowed: bool) -> None:
    if not allowed:
        raise ValueError("В этом состоянии назначение исполнителя запрещено")


def validate_employee_change(same_employee: bool) -> None:
    if same_employee:
        raise ValueError("Этот исполнитель уже назначен")


def validate_unique_employee_ids(employee_ids: tuple[str, ...]) -> None:
    if len(employee_ids) != len(set(employee_ids)):
        raise ValueError("Идентификаторы сотрудников должны различаться")


def validate_ticket_registration(
    already_registered: bool, new_unassigned: bool
) -> None:
    if already_registered:
        raise ValueError("Обращение уже зарегистрировано")
    if not new_unassigned:
        raise ValueError("Добавлять можно только новое обращение без исполнителя")


def validate_registered(exists: bool) -> None:
    if not exists:
        raise ValueError("Обращение не зарегистрировано")


def validate_found(value: T | None, message: str) -> T:
    if value is None:
        raise ValueError(message)
    return value

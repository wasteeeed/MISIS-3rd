# Валидация

from typing import TypeVar

T = TypeVar("T")


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


def validate_comment(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("Комментарий должен быть строкой")


def validate_type(value: object, expected_type: type, name: str) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Некорректный тип: {name}")


def validate_positive_int(value: int, name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} должен быть положительным целым числом")


def validate_participants(employee_ids: tuple[str, ...]) -> None:
    if not employee_ids:
        raise ValueError("У этапа должен быть хотя бы один участник")
    if len(employee_ids) != len(set(employee_ids)):
        raise ValueError("Участники одного этапа не должны повторяться")


def validate_approval_threshold(required: int, participant_count: int) -> None:
    validate_positive_int(required, "required_approvals")
    if required > participant_count:
        raise ValueError("Нельзя требовать больше согласований, чем участников этапа")


def validate_stages(nonempty: bool) -> None:
    if not nonempty:
        raise ValueError("В процессе должен быть хотя бы один этап")


def validate_process_active(active: bool) -> None:
    if not active:
        raise ValueError("Процесс сейчас не принимает решения участников")


def validate_new_decision(already_decided: bool) -> None:
    if already_decided:
        raise ValueError("Участник уже принял решение на этом этапе")


def validate_revision_allowed(requested: bool, is_author: bool) -> None:
    if not requested:
        raise ValueError("Исправление возможно только после запроса изменений")
    if not is_author:
        raise ValueError("Исправлять документ должен его автор")


def validate_found(value: T | None, message: str) -> T:
    if value is None:
        raise ValueError(message)
    return value

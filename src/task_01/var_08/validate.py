# Валидация

from datetime import datetime


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


def validate_optional_text(value: str | None, name: str) -> None:
    if value is not None:
        validate_text(value, name)


def validate_tags(values: frozenset[str], name: str) -> None:
    if not isinstance(values, (set, frozenset)):
        raise ValueError(f"{name} должен быть набором строк")
    for value in values:
        validate_text(value, name)


def validate_type(value: object, expected_type: type, name: str) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Некорректный тип: {name}")


def validate_time_range(starts_at: datetime, ends_at: datetime) -> None:
    validate_type(starts_at, datetime, "starts_at")
    validate_type(ends_at, datetime, "ends_at")
    if starts_at.tzinfo is not None or ends_at.tzinfo is not None:
        raise ValueError("Укажите местное время офиса без часового пояса")
    if starts_at >= ends_at:
        raise ValueError("Время окончания должно быть позже времени начала")


def validate_unique_workplace_ids(workplace_ids: tuple[str, ...]) -> None:
    if len(workplace_ids) != len(set(workplace_ids)):
        raise ValueError("Идентификаторы рабочих мест должны различаться")


def validate_workplace_registered(registered: bool) -> None:
    if not registered:
        raise ValueError("Рабочее место не зарегистрировано в сервисе")


def validate_registered(registered: bool) -> None:
    if not registered:
        raise ValueError("Бронирование не зарегистрировано")


def validate_booking_allowed(violations: tuple[str, ...]) -> None:
    if violations:
        raise ValueError("; ".join(violations))

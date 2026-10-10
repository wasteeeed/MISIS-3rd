# Модели и правила

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time

from validate import (
    validate_optional_text,
    validate_tags,
    validate_text,
    validate_time_range,
    validate_type,
)


@dataclass(frozen=True, slots=True)
class Employee:
    employee_id: str
    name: str
    department: str
    permissions: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        validate_text(self.employee_id, "employee_id")
        validate_text(self.name, "name")
        validate_text(self.department, "department")
        validate_tags(self.permissions, "permissions")
        object.__setattr__(self, "permissions", frozenset(self.permissions))


@dataclass(frozen=True, slots=True)
class Workplace:
    workplace_id: str
    name: str
    department: str | None = None
    required_permission: str | None = None
    features: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        validate_text(self.workplace_id, "workplace_id")
        validate_text(self.name, "name")
        validate_optional_text(self.department, "department")
        validate_optional_text(self.required_permission, "required_permission")
        validate_tags(self.features, "features")
        object.__setattr__(self, "features", frozenset(self.features))


@dataclass(frozen=True, slots=True, eq=False)
class Booking:
    employee: Employee
    workplace: Workplace
    starts_at: datetime
    ends_at: datetime
    required_features: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        validate_type(self.employee, Employee, "employee")
        validate_type(self.workplace, Workplace, "workplace")
        validate_time_range(self.starts_at, self.ends_at)
        validate_tags(self.required_features, "required_features")
        object.__setattr__(
            self, "required_features", frozenset(self.required_features)
        )


class BookingRule(ABC):
    @abstractmethod
    def check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> str | None:
        raise NotImplementedError


class NoOverlapRule(BookingRule):
    def check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> str | None:
        for existing in existing_bookings:
            if (
                existing.workplace.workplace_id == booking.workplace.workplace_id
                and booking.starts_at < existing.ends_at
                and existing.starts_at < booking.ends_at
            ):
                return "Место уже забронировано на это время"
        return None


class DepartmentRule(BookingRule):
    def check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> str | None:
        department = booking.workplace.department
        if department is not None and booking.employee.department != department:
            return f"Место доступно только отделу «{department}»"
        return None


class PermissionRule(BookingRule):
    def check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> str | None:
        permission = booking.workplace.required_permission
        if permission is not None and permission not in booking.employee.permissions:
            return f"Требуется разрешение «{permission}»"
        return None


class FeaturesRule(BookingRule):
    def check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> str | None:
        missing = booking.required_features - booking.workplace.features
        if missing:
            return "У места отсутствуют признаки: " + ", ".join(sorted(missing))
        return None


class WorkingHoursRule(BookingRule):
    def check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> str | None:
        if (
            booking.starts_at.date() != booking.ends_at.date()
            or booking.starts_at.time() < time(9)
            or booking.ends_at.time() > time(18)
        ):
            return "Бронирование разрешено с 09:00 до 18:00 в пределах одного дня"
        return None

# Управление бронированиями

from dataclasses import dataclass, field, replace
from datetime import datetime

from models import (
    Booking,
    BookingRule,
    DepartmentRule,
    Employee,
    FeaturesRule,
    NoOverlapRule,
    PermissionRule,
    Workplace,
)
from validate import (
    validate_booking_allowed,
    validate_registered,
    validate_tags,
    validate_time_range,
    validate_type,
    validate_unique_workplace_ids,
    validate_workplace_registered,
)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class BookingService:
    workplaces: tuple[Workplace, ...]
    extra_rules: tuple[BookingRule, ...] = ()
    __bookings: list[Booking] = field(default_factory=list, init=False)
    _rules: tuple[BookingRule, ...] = field(init=False)

    def __post_init__(self) -> None:
        workplaces = tuple(self.workplaces)
        extra_rules = tuple(self.extra_rules)
        for workplace in workplaces:
            validate_type(workplace, Workplace, "workplace")
        validate_unique_workplace_ids(tuple(p.workplace_id for p in workplaces))
        for rule in extra_rules:
            validate_type(rule, BookingRule, "rule")
        object.__setattr__(self, "workplaces", workplaces)
        object.__setattr__(self, "extra_rules", extra_rules)
        object.__setattr__(self, "_rules", (
            NoOverlapRule(), DepartmentRule(), PermissionRule(), FeaturesRule(),
            *extra_rules,
        ))

    def bookings(self) -> tuple[Booking, ...]:
        return tuple(self.__bookings)

    def check_booking(self, booking: Booking) -> tuple[str, ...]:
        return self._check(booking, self.bookings())

    def create_booking(self, booking: Booking) -> Booking:
        validate_booking_allowed(self.check_booking(booking))
        self.__bookings.append(booking)
        return booking

    def available_workplaces(
        self,
        employee: Employee,
        starts_at: datetime,
        ends_at: datetime,
        required_features: frozenset[str] = frozenset(),
    ) -> tuple[Workplace, ...]:
        validate_type(employee, Employee, "employee")
        validate_time_range(starts_at, ends_at)
        validate_tags(required_features, "required_features")
        existing = self.bookings()
        available: list[Workplace] = []
        for workplace in self.workplaces:
            candidate = Booking(
                employee, workplace, starts_at, ends_at, required_features
            )
            if not self._check(candidate, existing):
                available.append(workplace)
        return tuple(available)

    def reschedule(
        self, booking: Booking, starts_at: datetime, ends_at: datetime
    ) -> Booking:
        validate_type(booking, Booking, "booking")
        validate_registered(booking in self.__bookings)
        updated = replace(booking, starts_at=starts_at, ends_at=ends_at)
        remaining = tuple(b for b in self.__bookings if b is not booking)
        validate_booking_allowed(self._check(updated, remaining))
        self.__bookings[self.__bookings.index(booking)] = updated
        return updated

    def _check(
        self, booking: Booking, existing_bookings: tuple[Booking, ...]
    ) -> tuple[str, ...]:
        validate_type(booking, Booking, "booking")
        validate_workplace_registered(
            any(place is booking.workplace for place in self.workplaces)
        )
        violations: list[str] = []
        for rule in self._rules:
            violation = rule.check(booking, existing_bookings)
            if violation is not None:
                violations.append(violation)
        return tuple(violations)

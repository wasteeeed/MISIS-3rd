# Транспорт и аренда

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from validate import (
    CENT,
    validate_available,
    validate_boolean,
    validate_datetime,
    validate_duration,
    validate_license,
    validate_minimum_age,
    validate_money,
    validate_optional_percent,
    validate_positive_int,
    validate_registered,
    validate_return_level,
    validate_text,
    validate_time_range,
    validate_type,
)


@dataclass(frozen=True, slots=True)
class User:
    name: str
    age: int
    has_license: bool = False

    def __post_init__(self) -> None:
        validate_text(self.name, "name")
        validate_positive_int(self.age, "age")
        validate_boolean(self.has_license, "has_license")


@dataclass(frozen=True, slots=True)
class ReturnInfo:
    fuel_percent: int | None = None
    battery_percent: int | None = None

    def __post_init__(self) -> None:
        validate_optional_percent(self.fuel_percent, "fuel_percent")
        validate_optional_percent(self.battery_percent, "battery_percent")


@dataclass(frozen=True, slots=True, eq=False)
class Rental:
    transport: Transport
    user: User
    starts_at: datetime
    ends_at: datetime | None = field(default=None, init=False)
    total: Decimal | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        validate_type(self.transport, Transport, "transport")
        validate_type(self.user, User, "user")
        validate_datetime(self.starts_at, "starts_at")


def _seconds(duration: timedelta) -> Decimal:
    return (
        Decimal(duration.days * 86400 + duration.seconds)
        + Decimal(duration.microseconds) / 1000000
    )


@dataclass(frozen=True, slots=True, eq=False)
class Transport(ABC):
    transport_id: str
    name: str
    __rental: Rental | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        validate_text(self.transport_id, "transport_id")
        validate_text(self.name, "name")

    @property
    def is_available(self) -> bool:
        return self.__rental is None

    def rent(self, user: User, starts_at: datetime) -> Rental:
        rental = Rental(self, user, starts_at)
        validate_available(self.is_available)
        self._check_rental_conditions(user)
        object.__setattr__(self, "_Transport__rental", rental)
        return rental

    def return_back(
        self, rental: Rental, ends_at: datetime, info: ReturnInfo
    ) -> Decimal:
        validate_type(rental, Rental, "rental")
        validate_registered(
            self.__rental is rental, "Эта аренда не является активной для транспорта"
        )
        validate_time_range(rental.starts_at, ends_at)
        validate_type(info, ReturnInfo, "return_info")
        self._check_return_conditions(info)
        total = self.calculate_cost(ends_at - rental.starts_at)
        object.__setattr__(rental, "ends_at", ends_at)
        object.__setattr__(rental, "total", total)
        object.__setattr__(self, "_Transport__rental", None)
        return total

    def calculate_cost(self, duration: timedelta) -> Decimal:
        validate_duration(duration)
        return self._calculate_cost(duration).quantize(CENT, rounding=ROUND_HALF_UP)

    @abstractmethod
    def _calculate_cost(self, duration: timedelta) -> Decimal:
        raise NotImplementedError

    def _check_rental_conditions(self, user: User) -> None:
        pass

    def _check_return_conditions(self, info: ReturnInfo) -> None:
        pass


@dataclass(frozen=True, slots=True, eq=False)
class Bicycle(Transport):
    hourly_rate: Decimal = Decimal("120.00")

    def __post_init__(self) -> None:
        Transport.__post_init__(self)
        validate_money(self.hourly_rate, "hourly_rate")

    def _calculate_cost(self, duration: timedelta) -> Decimal:
        return self.hourly_rate * _seconds(duration) / 3600


@dataclass(frozen=True, slots=True, eq=False)
class Car(Transport):
    hourly_rate: Decimal = Decimal("500.00")

    def __post_init__(self) -> None:
        Transport.__post_init__(self)
        validate_money(self.hourly_rate, "hourly_rate")

    def _calculate_cost(self, duration: timedelta) -> Decimal:
        hours = (_seconds(duration) / 3600).to_integral_value(rounding=ROUND_CEILING)
        return self.hourly_rate * hours

    def _check_rental_conditions(self, user: User) -> None:
        validate_minimum_age(user.age, 18)
        validate_license(user.has_license)

    def _check_return_conditions(self, info: ReturnInfo) -> None:
        validate_return_level(info.fuel_percent, 20, "уровень топлива")


@dataclass(frozen=True, slots=True, eq=False)
class ElectricScooter(Transport):
    minute_rate: Decimal = Decimal("10.00")
    unlock_fee: Decimal = Decimal("50.00")

    def __post_init__(self) -> None:
        Transport.__post_init__(self)
        validate_money(self.minute_rate, "minute_rate")
        validate_money(self.unlock_fee, "unlock_fee", allow_zero=True)

    def _calculate_cost(self, duration: timedelta) -> Decimal:
        minutes = (_seconds(duration) / 60).to_integral_value(rounding=ROUND_CEILING)
        return self.unlock_fee + self.minute_rate * minutes

    def _check_rental_conditions(self, user: User) -> None:
        validate_minimum_age(user.age, 16)

    def _check_return_conditions(self, info: ReturnInfo) -> None:
        validate_return_level(info.battery_percent, 20, "заряд батареи")

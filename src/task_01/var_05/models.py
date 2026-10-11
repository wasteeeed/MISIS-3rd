# Сотрудники

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from validate import (
    CENT,
    validate_decimal,
    validate_money,
    validate_month,
    validate_text,
)

ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class Employee(ABC):
    employee_id: str
    name: str
    month: date
    bonus: Decimal = field(default=ZERO, kw_only=True)

    def __post_init__(self) -> None:
        validate_text(self.employee_id, "employee_id")
        validate_text(self.name, "name")
        validate_month(self.month)
        validate_money(self.bonus, "bonus", allow_zero=True)

    @abstractmethod
    def _base_pay(self) -> Decimal:
        raise NotImplementedError

    def calculate_salary(self) -> Decimal:
        return (self._base_pay() + self.bonus).quantize(CENT, rounding=ROUND_HALF_UP)

    def get_brief_info(self) -> str:
        return (
            f"{self.employee_id}: {self.name}, месяц {self.month:%Y-%m}, "
            f"выплата {self.calculate_salary():.2f}"
        )


@dataclass(frozen=True, slots=True)
class SalariedEmployee(Employee):
    monthly_salary: Decimal

    def __post_init__(self) -> None:
        Employee.__post_init__(self)
        validate_money(self.monthly_salary, "monthly_salary")

    def _base_pay(self) -> Decimal:
        return self.monthly_salary


@dataclass(frozen=True, slots=True)
class HourlyEmployee(Employee):
    hourly_rate: Decimal
    hours_worked: Decimal

    def __post_init__(self) -> None:
        Employee.__post_init__(self)
        validate_money(self.hourly_rate, "hourly_rate")
        validate_decimal(self.hours_worked, "hours_worked", allow_zero=True)

    def _base_pay(self) -> Decimal:
        return self.hourly_rate * self.hours_worked


@dataclass(frozen=True, slots=True)
class Manager(Employee):
    monthly_salary: Decimal
    kpi_multiplier: Decimal

    def __post_init__(self) -> None:
        Employee.__post_init__(self)
        validate_money(self.monthly_salary, "monthly_salary")
        validate_decimal(self.kpi_multiplier, "kpi_multiplier", allow_zero=True)

    def _base_pay(self) -> Decimal:
        return self.monthly_salary * self.kpi_multiplier

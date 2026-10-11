# Подразделение

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from models import Employee, ZERO
from validate import validate_month, validate_registration, validate_text, validate_type


@dataclass(frozen=True, slots=True, eq=False)
class Department:
    name: str
    month: date
    __employees: dict[str, Employee] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        validate_text(self.name, "name")
        validate_month(self.month)

    def add_employee(self, employee: Employee) -> None:
        validate_type(employee, Employee, "employee")
        validate_registration(
            employee.month, self.month, employee.employee_id in self.__employees
        )
        self.__employees[employee.employee_id] = employee

    def employees(self) -> tuple[Employee, ...]:
        return tuple(self.__employees.values())

    def calculate_total_payroll(self) -> Decimal:
        return sum((employee.calculate_salary() for employee in self.employees()), ZERO)

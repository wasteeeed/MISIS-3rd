# Демонстрация

from dataclasses import replace
from datetime import date
from decimal import Decimal

from main import Department
from models import HourlyEmployee, Manager, SalariedEmployee


def scenario_01() -> None:
    print("\nСценарий 1: выплаты сотрудникам разных категорий")
    department = Department("Разработка", date(2026, 10, 1))
    employees = (
        SalariedEmployee(
            "E-1", "Анна", department.month, Decimal("60000.00"),
            bonus=Decimal("5000.00"),
        ),
        HourlyEmployee(
            "E-2", "Дмитрий", department.month, Decimal("750.00"), Decimal("120")
        ),
        Manager(
            "E-3", "Марина", department.month, Decimal("80000.00"), Decimal("1.25"),
            bonus=Decimal("10000.00"),
        ),
    )
    for employee in employees:
        department.add_employee(employee)
        print(employee.get_brief_info())
    assert department.employees() == employees
    assert tuple(employee.calculate_salary() for employee in employees) == (
        Decimal("65000.00"), Decimal("90000.00"), Decimal("110000.00")
    )
    assert department.calculate_total_payroll() == Decimal("265000.00")
    print(f"Итого по подразделению: {department.calculate_total_payroll():.2f}")


def scenario_02() -> None:
    print("\nСценарий 2: независимый расчет за два месяца")
    october = Department("Поддержка", date(2026, 10, 1))
    november = Department("Поддержка", date(2026, 11, 1))
    rate = Decimal("1000.10")
    october_employee = HourlyEmployee(
        "E-1", "Олег", october.month, rate, Decimal("10.25")
    )
    november_employee = HourlyEmployee(
        "E-1", "Олег", november.month, rate, Decimal("4")
    )
    october.add_employee(october_employee)
    assert november.calculate_total_payroll() == Decimal("0.00")
    november.add_employee(november_employee)
    assert october.calculate_total_payroll() == Decimal("10251.03")
    assert november.calculate_total_payroll() == Decimal("4000.40")
    for employee in (october_employee, november_employee):
        print(employee.get_brief_info())
        print(f"Часов за месяц: {employee.hours_worked}")
    assert october.calculate_total_payroll() == Decimal("10251.03")
    print("Повторный расчет не меняет часы и выплаты")


def scenario_03() -> None:
    print("\nСценарий 3: отклонение некорректных данных")
    department = Department("Продажи", date(2026, 10, 1))
    employee = SalariedEmployee("E-1", "Ирина", department.month, Decimal("60000.00"))
    department.add_employee(employee)
    before = (department.employees(), department.calculate_total_payroll())
    rejected_actions = (
        ("Пустое имя", lambda: replace(employee, name=" ")),
        ("Отрицательная премия", lambda: replace(employee, bonus=Decimal("-1"))),
        (
            "Отрицательные часы",
            lambda: HourlyEmployee(
                "E-2", "Иван", department.month, Decimal("500.00"), Decimal("-1")
            ),
        ),
        ("Повторный сотрудник", lambda: department.add_employee(employee)),
        (
            "Другой месяц",
            lambda: department.add_employee(
                replace(employee, employee_id="E-2", month=date(2026, 11, 1))
            ),
        ),
    )
    for label, action in rejected_actions:
        try:
            action()
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
        assert (department.employees(), department.calculate_total_payroll()) == before
    print(
        f"После отказов: сотрудников {len(department.employees())}, "
        f"выплата {department.calculate_total_payroll():.2f}"
    )


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

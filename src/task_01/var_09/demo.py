# Демонстрация

from main import AssignmentService, TicketRegistry
from models import Employee, Priority, Ticket, TicketStatus


def scenario_01() -> None:
    print("\nСценарий 1: выбор исполнителя и обработка обращения")
    registry = TicketRegistry()
    employees = (
        Employee("E-1", "Ирина", frozenset({"payments"})),
        Employee("E-2", "Анна", frozenset({"technical"})),
        Employee("E-3", "Борис", frozenset({"technical"})),
    )
    service = AssignmentService(registry, employees)
    busy_ticket = Ticket("USER-1", "Не работает принтер", "technical")
    registry.add(busy_ticket)
    busy_employee = service.assign(busy_ticket)
    assert busy_employee is employees[1]

    ticket = Ticket("USER-2", "Не подключается Wi-Fi", "technical")
    registry.add(ticket)
    employee = service.assign(ticket)
    assert employee is employees[2]
    print("Исполнитель:", employee.name)

    steps = (
        (ticket.start_work, TicketStatus.IN_PROGRESS),
        (ticket.wait_for_user, TicketStatus.WAITING_FOR_USER),
        (ticket.receive_user_response, TicketStatus.IN_PROGRESS),
        (ticket.close, TicketStatus.CLOSED),
    )
    for action, expected in steps:
        action()
        assert ticket.status is expected
        expected_load = 0 if expected is TicketStatus.CLOSED else 1
        assert registry.workload(employee) == expected_load
        print("Состояние:", ticket.status.value)
    assert registry.workload(employees[1]) == 1
    print("Загрузка исполнителя:", registry.workload(employee))


def scenario_02() -> None:
    print("\nСценарий 2: приоритет, особые требования и передача обращения")
    registry = TicketRegistry()
    employees = (
        Employee(
            "E-1", "Алексей", frozenset({"technical"}),
            max_priority=Priority.HIGH,
        ),
        Employee("E-2", "Елена", frozenset({"technical"}), is_senior=True),
        Employee(
            "E-3", "Мария", frozenset({"technical"}),
            max_priority=Priority.HIGH, is_senior=True,
        ),
        Employee(
            "E-4", "Олег", frozenset({"technical"}),
            max_priority=Priority.HIGH, is_senior=True,
        ),
    )
    service = AssignmentService(registry, employees)
    ticket = Ticket(
        "USER-3", "Недоступен рабочий сервер", "technical",
        priority=Priority.HIGH, requires_senior=True,
    )
    registry.add(ticket)
    first_employee = service.assign(ticket)
    assert first_employee is employees[2]
    ticket.start_work()

    second_employee = service.assign(ticket)
    assert second_employee is employees[3]
    assert ticket.status is TicketStatus.IN_PROGRESS
    assert registry.workload(first_employee) == 0
    assert registry.workload(second_employee) == 1
    print(f"Передача: {first_employee.name} -> {second_employee.name}")
    ticket.close()
    assert registry.workload(second_employee) == 0
    print("После закрытия:", ticket.status.value)


def scenario_03() -> None:
    print("\nСценарий 3: отказы без изменения состояния и загрузки")
    registry = TicketRegistry()
    employee = Employee("E-1", "Ирина", frozenset({"payments"}), max_load=1)
    service = AssignmentService(registry, (employee,))
    first = Ticket("USER-4", "Не прошёл платёж", "payments")
    second = Ticket("USER-5", "Не пришёл возврат", "payments")
    registry.add(first)
    registry.add(second)
    service.assign(first)
    first.start_work()
    first.wait_for_user()
    before = (first.status, first.employee, second.status, second.employee)
    rejected_actions = (
        ("Превышение загрузки", lambda: service.assign(second)),
        ("Повторное начало работы", first.start_work),
        ("Закрытие до ответа пользователя", first.close),
        ("Передача во время ожидания", lambda: service.assign(first)),
    )
    for label, action in rejected_actions:
        try:
            action()
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
        assert (first.status, first.employee, second.status, second.employee) == before
        assert registry.workload(employee) == 1

    first.receive_user_response()
    first.close()
    next_employee = service.assign(second)
    assert next_employee is employee
    assert registry.workload(employee) == 1
    print("После освобождения места назначено:", second.title)


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

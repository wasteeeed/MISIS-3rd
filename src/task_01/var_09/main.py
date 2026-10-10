# Распределение обращений

from dataclasses import dataclass, field
from uuid import UUID

from models import (
    AssignmentRule,
    Employee,
    PriorityRule,
    SeniorRule,
    SpecializationRule,
    Ticket,
    TicketStatus,
    WorkloadRule,
)
from validate import (
    validate_assignment_allowed,
    validate_found,
    validate_registered,
    validate_ticket_registration,
    validate_type,
    validate_unique_employee_ids,
)


# Контейнер
@dataclass(slots=True, eq=False, repr=False)
class TicketRegistry:
    __tickets: dict[UUID, Ticket] = field(default_factory=dict, init=False)

    def add(self, ticket: Ticket) -> None:
        validate_type(ticket, Ticket, "ticket")
        validate_ticket_registration(
            ticket.id in self.__tickets,
            ticket.status is TicketStatus.NEW and ticket.employee is None,
        )
        self.__tickets[ticket.id] = ticket

    def contains(self, ticket: Ticket) -> bool:
        validate_type(ticket, Ticket, "ticket")
        return self.__tickets.get(ticket.id) is ticket

    def workload(self, employee: Employee) -> int:
        validate_type(employee, Employee, "employee")
        return sum(
            ticket.employee is not None
            and ticket.employee.employee_id == employee.employee_id
            and ticket.status is not TicketStatus.CLOSED
            for ticket in self.__tickets.values()
        )


@dataclass(frozen=True, slots=True)
class AssignmentService:
    registry: TicketRegistry
    employees: tuple[Employee, ...]
    extra_rules: tuple[AssignmentRule, ...] = ()
    _rules: tuple[AssignmentRule, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        validate_type(self.registry, TicketRegistry, "registry")
        employees = tuple(self.employees)
        extra_rules = tuple(self.extra_rules)
        for employee in employees:
            validate_type(employee, Employee, "employee")
        validate_unique_employee_ids(tuple(e.employee_id for e in employees))
        for rule in extra_rules:
            validate_type(rule, AssignmentRule, "rule")
        object.__setattr__(self, "employees", employees)
        object.__setattr__(self, "extra_rules", extra_rules)
        object.__setattr__(self, "_rules", (
            SpecializationRule(), WorkloadRule(), PriorityRule(), SeniorRule(),
            *extra_rules,
        ))

    def find_employee(self, ticket: Ticket) -> Employee | None:
        validate_type(ticket, Ticket, "ticket")
        best: Employee | None = None
        best_load = 0
        for employee in self.employees:
            if (
                ticket.employee is not None
                and employee.employee_id == ticket.employee.employee_id
            ):
                continue
            current_load = self.registry.workload(employee)
            if all(rule.allows(ticket, employee, current_load) for rule in self._rules):
                if best is None or current_load < best_load:
                    best, best_load = employee, current_load
        return best

    def assign(self, ticket: Ticket) -> Employee:
        validate_registered(self.registry.contains(ticket))
        validate_assignment_allowed(ticket.can_assign())
        employee = validate_found(
            self.find_employee(ticket), "Подходящий исполнитель не найден"
        )
        ticket._assign(employee)
        return employee

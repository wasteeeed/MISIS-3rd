# Модели и правила

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from uuid import UUID, uuid4

from validate import (
    validate_assignee,
    validate_assignment_allowed,
    validate_boolean,
    validate_employee_change,
    validate_positive_int,
    validate_specializations,
    validate_text,
    validate_transition,
    validate_type,
)


class Priority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3


class TicketStatus(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class Employee:
    employee_id: str
    name: str
    specializations: frozenset[str]
    max_load: int = 3
    max_priority: Priority = Priority.NORMAL
    is_senior: bool = False

    def __post_init__(self) -> None:
        validate_text(self.employee_id, "employee_id")
        validate_text(self.name, "name")
        validate_specializations(self.specializations)
        validate_positive_int(self.max_load, "max_load")
        validate_type(self.max_priority, Priority, "max_priority")
        validate_boolean(self.is_senior, "is_senior")
        object.__setattr__(self, "specializations", frozenset(self.specializations))


@dataclass(frozen=True, slots=True, eq=False)
class Ticket:
    user_id: str
    title: str
    specialization: str
    priority: Priority = Priority.NORMAL
    requires_senior: bool = False
    id: UUID = field(default_factory=uuid4, init=False, repr=False)
    status: TicketStatus = field(
        default=TicketStatus.NEW, init=False, repr=False
    )
    employee: Employee | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        validate_text(self.user_id, "user_id")
        validate_text(self.title, "title")
        validate_text(self.specialization, "specialization")
        validate_type(self.priority, Priority, "priority")
        validate_boolean(self.requires_senior, "requires_senior")

    def can_assign(self) -> bool:
        return self.status in (TicketStatus.NEW, TicketStatus.IN_PROGRESS)

    def _assign(self, employee: Employee) -> None:
        validate_type(employee, Employee, "employee")
        validate_assignment_allowed(self.can_assign())
        validate_employee_change(
            self.employee is not None
            and self.employee.employee_id == employee.employee_id
        )
        object.__setattr__(self, "employee", employee)

    def start_work(self) -> None:
        self._transition(TicketStatus.NEW, TicketStatus.IN_PROGRESS)

    def wait_for_user(self) -> None:
        self._transition(TicketStatus.IN_PROGRESS, TicketStatus.WAITING_FOR_USER)

    def receive_user_response(self) -> None:
        self._transition(TicketStatus.WAITING_FOR_USER, TicketStatus.IN_PROGRESS)

    def close(self) -> None:
        self._transition(TicketStatus.IN_PROGRESS, TicketStatus.CLOSED)

    def _transition(self, expected: TicketStatus, target: TicketStatus) -> None:
        validate_transition(self.status.value, expected.value, target.value)
        validate_assignee(self.employee is not None)
        object.__setattr__(self, "status", target)


class AssignmentRule(ABC):
    @abstractmethod
    def allows(self, ticket: Ticket, employee: Employee, current_load: int) -> bool:
        raise NotImplementedError


class SpecializationRule(AssignmentRule):
    def allows(self, ticket: Ticket, employee: Employee, current_load: int) -> bool:
        return ticket.specialization in employee.specializations


class WorkloadRule(AssignmentRule):
    def allows(self, ticket: Ticket, employee: Employee, current_load: int) -> bool:
        return current_load < employee.max_load


class PriorityRule(AssignmentRule):
    def allows(self, ticket: Ticket, employee: Employee, current_load: int) -> bool:
        return ticket.priority <= employee.max_priority


class SeniorRule(AssignmentRule):
    def allows(self, ticket: Ticket, employee: Employee, current_load: int) -> bool:
        return not ticket.requires_senior or employee.is_senior

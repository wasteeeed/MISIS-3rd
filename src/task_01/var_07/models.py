# Модели и правила

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from validate import (
    validate_approval_threshold,
    validate_comment,
    validate_participants,
    validate_positive_int,
    validate_text,
    validate_type,
)


@dataclass(frozen=True, slots=True)
class Employee:
    employee_id: str
    name: str

    def __post_init__(self) -> None:
        validate_text(self.employee_id, "employee_id")
        validate_text(self.name, "name")


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    title: str
    author: Employee
    content: str
    revision: int = 1

    def __post_init__(self) -> None:
        validate_text(self.document_id, "document_id")
        validate_text(self.title, "title")
        validate_type(self.author, Employee, "author")
        validate_text(self.content, "content")
        validate_positive_int(self.revision, "revision")


class Decision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ApprovalStatus(Enum):
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    participant: Employee
    decision: Decision
    comment: str = ""

    def __post_init__(self) -> None:
        validate_type(self.participant, Employee, "participant")
        validate_type(self.decision, Decision, "decision")
        validate_comment(self.comment)


class CompletionRule(ABC):
    @abstractmethod
    def required_approvals(self, participant_count: int) -> int:
        raise NotImplementedError

    def evaluate(
        self, decisions: tuple[Decision, ...], participant_count: int
    ) -> ApprovalStatus:
        required = self.required_approvals(participant_count)
        validate_approval_threshold(required, participant_count)
        if Decision.REJECT in decisions:
            return ApprovalStatus.REJECTED
        if Decision.REQUEST_CHANGES in decisions:
            return ApprovalStatus.CHANGES_REQUESTED
        if decisions.count(Decision.APPROVE) >= required:
            return ApprovalStatus.APPROVED
        return ApprovalStatus.IN_PROGRESS


class AllApprovalsRule(CompletionRule):
    def required_approvals(self, participant_count: int) -> int:
        return participant_count


class AnyApprovalRule(CompletionRule):
    def required_approvals(self, participant_count: int) -> int:
        return 1


@dataclass(frozen=True, slots=True)
class QuorumRule(CompletionRule):
    minimum_approvals: int

    def __post_init__(self) -> None:
        validate_positive_int(self.minimum_approvals, "minimum_approvals")

    def required_approvals(self, participant_count: int) -> int:
        return self.minimum_approvals


@dataclass(frozen=True, slots=True)
class ApprovalStage:
    name: str
    participants: tuple[Employee, ...]
    rule: CompletionRule = field(default_factory=AllApprovalsRule)

    def __post_init__(self) -> None:
        validate_text(self.name, "name")
        participants = tuple(self.participants)
        for participant in participants:
            validate_type(participant, Employee, "participant")
        validate_participants(tuple(p.employee_id for p in participants))
        validate_type(self.rule, CompletionRule, "rule")
        validate_approval_threshold(
            self.rule.required_approvals(len(participants)), len(participants)
        )
        object.__setattr__(self, "participants", participants)

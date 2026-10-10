# Управление согласованием

from dataclasses import dataclass, field, replace

from models import (
    ApprovalStage,
    ApprovalStatus,
    Decision,
    DecisionRecord,
    Document,
)
from validate import (
    validate_found,
    validate_new_decision,
    validate_process_active,
    validate_revision_allowed,
    validate_stages,
    validate_text,
    validate_type,
)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ApprovalProcess:
    document: Document
    stages: tuple[ApprovalStage, ...]
    status: ApprovalStatus = field(default=ApprovalStatus.IN_PROGRESS, init=False)
    __stage_index: int = field(default=0, init=False)
    __decisions: list[DecisionRecord] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        validate_type(self.document, Document, "document")
        stages = tuple(self.stages)
        validate_stages(bool(stages))
        for stage in stages:
            validate_type(stage, ApprovalStage, "stage")
        object.__setattr__(self, "stages", stages)

    @property
    def current_stage(self) -> ApprovalStage | None:
        if self.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
            return None
        return self.stages[self.__stage_index]

    def decisions(self) -> tuple[DecisionRecord, ...]:
        return tuple(self.__decisions)

    def decide(
        self, participant_id: str, decision: Decision, comment: str = ""
    ) -> None:
        validate_process_active(self.status is ApprovalStatus.IN_PROGRESS)
        validate_text(participant_id, "participant_id")
        stage = validate_found(self.current_stage, "Нет текущего этапа")
        participant = validate_found(
            next(
                (p for p in stage.participants if p.employee_id == participant_id), None
            ),
            "Участник не назначен на текущий этап",
        )
        validate_new_decision(
            any(
                record.participant.employee_id == participant_id
                for record in self.__decisions
            )
        )
        record = DecisionRecord(participant, decision, comment)
        candidate = (*self.decisions(), record)
        result = stage.rule.evaluate(
            tuple(record.decision for record in candidate), len(stage.participants)
        )
        validate_type(result, ApprovalStatus, "stage_result")
        self.__decisions.append(record)
        if result is ApprovalStatus.APPROVED:
            next_index = self.__stage_index + 1
            if next_index < len(self.stages):
                object.__setattr__(self, "_ApprovalProcess__stage_index", next_index)
                self.__decisions.clear()
            else:
                object.__setattr__(self, "status", ApprovalStatus.APPROVED)
        else:
            object.__setattr__(self, "status", result)

    def revise(self, author_id: str, content: str) -> None:
        validate_text(author_id, "author_id")
        validate_revision_allowed(
            self.status is ApprovalStatus.CHANGES_REQUESTED,
            author_id == self.document.author.employee_id,
        )
        updated = replace(
            self.document, content=content, revision=self.document.revision + 1
        )
        object.__setattr__(self, "document", updated)
        object.__setattr__(self, "_ApprovalProcess__stage_index", 0)
        self.__decisions.clear()
        object.__setattr__(self, "status", ApprovalStatus.IN_PROGRESS)

    def next_action(self) -> str:
        if self.status is ApprovalStatus.APPROVED:
            return "Документ согласован; можно публиковать"
        if self.status is ApprovalStatus.REJECTED:
            return "Процесс отклонён; дальнейшее согласование прекращено"
        if self.status is ApprovalStatus.CHANGES_REQUESTED:
            return f"Автор {self.document.author.name} должен исправить документ"
        stage = validate_found(self.current_stage, "Нет текущего этапа")
        decided = {record.participant.employee_id for record in self.__decisions}
        pending = ", ".join(
            p.name for p in stage.participants if p.employee_id not in decided
        )
        return f"Этап «{stage.name}»: ожидаются решения — {pending}"

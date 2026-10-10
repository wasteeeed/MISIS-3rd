# Демонстрация

from main import ApprovalProcess
from models import (
    AnyApprovalRule,
    ApprovalStage,
    ApprovalStatus,
    Decision,
    Document,
    Employee,
    QuorumRule,
)


def scenario_01() -> None:
    print("\nСценарий 1: последовательные этапы и разные правила")
    author = Employee("E-1", "Анна")
    lawyer = Employee("E-2", "Борис")
    manager = Employee("E-3", "Мария")
    editor = Employee("E-4", "Олег")
    document = Document("D-1", "Регламент", author, "Правила работы отдела")
    stages = (
        ApprovalStage("Юридическая проверка", (lawyer,)),
        ApprovalStage("Руководство", (manager, editor)),
        ApprovalStage("Публикация", (manager, editor), AnyApprovalRule()),
    )
    process = ApprovalProcess(document, stages)
    print(process.next_action())
    process.decide(lawyer.employee_id, Decision.APPROVE)
    assert process.current_stage is stages[1]
    process.decide(manager.employee_id, Decision.APPROVE)
    assert process.current_stage is stages[1]
    print(process.next_action())
    process.decide(editor.employee_id, Decision.APPROVE)
    assert process.current_stage is stages[2]
    print(process.next_action())
    process.decide(editor.employee_id, Decision.APPROVE)
    assert process.status is ApprovalStatus.APPROVED
    assert process.current_stage is None
    print("Результат:", process.status.value)
    print(process.next_action())


def scenario_02() -> None:
    print("\nСценарий 2: возврат автору и повторное согласование")
    author = Employee("E-1", "Анна")
    lawyer = Employee("E-2", "Борис")
    manager = Employee("E-3", "Мария")
    original = Document("D-2", "Договор", author, "Первая редакция договора")
    stages = (
        ApprovalStage("Юрист", (lawyer,)),
        ApprovalStage("Руководитель", (manager,)),
    )
    process = ApprovalProcess(original, stages)
    process.decide(lawyer.employee_id, Decision.APPROVE)
    process.decide(manager.employee_id, Decision.REQUEST_CHANGES, "Уточнить срок")
    assert process.status is ApprovalStatus.CHANGES_REQUESTED
    assert process.current_stage is stages[1]
    print("Замечание:", process.decisions()[0].comment)
    print(process.next_action())
    process.revise(author.employee_id, "Договор с уточнённым сроком")
    assert process.document.revision == 2
    assert original.revision == 1 and original.content == "Первая редакция договора"
    assert process.current_stage is stages[0] and process.decisions() == ()
    print("Редакция:", process.document.revision)
    print("Повторный запуск:", process.next_action())
    process.decide(lawyer.employee_id, Decision.APPROVE)
    process.decide(manager.employee_id, Decision.APPROVE)
    assert process.status is ApprovalStatus.APPROVED
    print("После исправления:", process.status.value)


def scenario_03() -> None:
    print("\nСценарий 3: кворум, неверные решения и отклонение")
    author = Employee("E-1", "Анна")
    participants = (
        Employee("E-2", "Борис"),
        Employee("E-3", "Мария"),
        Employee("E-4", "Олег"),
    )
    stages = (
        ApprovalStage("Комиссия", participants, QuorumRule(2)),
        ApprovalStage("Финальная проверка", (participants[2],)),
    )
    process = ApprovalProcess(
        Document("D-3", "Положение", author, "Проект положения"), stages
    )
    process.decide(participants[0].employee_id, Decision.APPROVE)
    before = (
        process.status, process.current_stage, process.decisions(), process.document
    )
    rejected_actions = (
        (
            "Посторонний участник",
            lambda: process.decide(author.employee_id, Decision.APPROVE),
        ),
        (
            "Повторное решение",
            lambda: process.decide(participants[0].employee_id, Decision.APPROVE),
        ),
        (
            "Правка без запроса",
            lambda: process.revise(author.employee_id, "Другой текст"),
        ),
    )
    for label, action in rejected_actions:
        try:
            action()
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
        assert (
            process.status, process.current_stage, process.decisions(), process.document
        ) == before
    process.decide(participants[1].employee_id, Decision.APPROVE)
    assert process.current_stage is stages[1]
    print("После двух согласований:", process.current_stage.name)
    process.decide(
        participants[2].employee_id, Decision.REJECT, "Публикация не разрешена"
    )
    assert process.status is ApprovalStatus.REJECTED
    print("Причина:", process.decisions()[0].comment)
    try:
        process.decide(participants[2].employee_id, Decision.APPROVE)
    except ValueError as error:
        print("Решение после отклонения:", error)
    else:
        raise AssertionError("Ожидался отказ после отклонения")
    assert process.status is ApprovalStatus.REJECTED
    print(process.next_action())


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

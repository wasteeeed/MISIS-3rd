# Демонстрация

from datetime import datetime

from main import BookingService
from models import Booking, Employee, Workplace, WorkingHoursRule


def scenario_01() -> None:
    print("\nСценарий 1: создание бронирований и границы интервалов")
    workplace = Workplace("W-1", "Общее место", features=frozenset({"monitor"}))
    anna = Employee("E-1", "Анна", "IT")
    boris = Employee("E-2", "Борис", "HR")
    service = BookingService((workplace,))
    first = Booking(
        anna, workplace, datetime(2026, 10, 12, 9), datetime(2026, 10, 12, 11),
        required_features=frozenset({"monitor"}),
    )
    second = Booking(
        boris, workplace, datetime(2026, 10, 12, 11), datetime(2026, 10, 12, 12)
    )
    next_day = Booking(
        anna, workplace, datetime(2026, 10, 13, 9), datetime(2026, 10, 13, 11)
    )
    for booking in (first, second, next_day):
        created = service.create_booking(booking)
        assert created is booking
        print(
            f"{booking.employee.name}: {booking.workplace.name}, "
            f"{booking.starts_at:%d.%m.%Y %H:%M}–{booking.ends_at:%H:%M}"
        )
    assert service.bookings() == (first, second, next_day)
    print("Количество бронирований:", len(service.bookings()))


def scenario_02() -> None:
    print("\nСценарий 2: поиск мест и несколько причин отказа")
    common = Workplace("W-1", "Общее место", features=frozenset({"monitor"}))
    department = Workplace(
        "W-2", "Место отдела IT", department="IT",
        features=frozenset({"monitor", "quiet"}),
    )
    restricted = Workplace(
        "W-3", "Закрытая зона", department="IT", required_permission="secure",
        features=frozenset({"monitor", "quiet"}),
    )
    basic = Workplace("W-4", "Место без монитора", features=frozenset({"quiet"}))
    anna = Employee("E-1", "Анна", "IT", permissions=frozenset({"secure"}))
    boris = Employee("E-2", "Борис", "HR")
    service = BookingService((common, department, restricted, basic))
    service.create_booking(Booking(
        boris, common, datetime(2026, 10, 12, 9), datetime(2026, 10, 12, 12)
    ))
    service.create_booking(Booking(
        anna, restricted, datetime(2026, 10, 12, 9), datetime(2026, 10, 12, 10)
    ))

    available = service.available_workplaces(
        anna, datetime(2026, 10, 12, 10), datetime(2026, 10, 12, 12),
        required_features=frozenset({"monitor", "quiet"}),
    )
    assert available == (department, restricted)
    print("Доступные места:", ", ".join(place.name for place in available))

    candidate = Booking(
        boris, restricted,
        datetime(2026, 10, 12, 9, 30), datetime(2026, 10, 12, 10, 30),
        required_features=frozenset({"standing_desk"}),
    )
    before = service.bookings()
    violations = service.check_booking(candidate)
    assert len(violations) == 4
    print("Причины отказа:")
    for violation in violations:
        print("-", violation)
    try:
        service.create_booking(candidate)
    except ValueError:
        print("Бронирование отклонено")
    else:
        raise AssertionError("Ожидался отказ при бронировании")
    assert service.bookings() == before
    print("Количество бронирований после отказа:", len(service.bookings()))


def scenario_03() -> None:
    print("\nСценарий 3: дополнительное правило и перенос бронирования")
    workplace = Workplace("W-1", "Место отдела IT", department="IT")
    anna = Employee("E-1", "Анна", "IT")
    boris = Employee("E-2", "Борис", "IT")
    service = BookingService((workplace,), extra_rules=(WorkingHoursRule(),))
    first = service.create_booking(Booking(
        anna, workplace, datetime(2026, 10, 12, 9), datetime(2026, 10, 12, 11)
    ))
    moved = service.reschedule(
        first, datetime(2026, 10, 12, 10), datetime(2026, 10, 12, 12)
    )
    assert service.bookings() == (moved,)
    assert first not in service.bookings()
    print(
        f"Перенос: {first.starts_at:%H:%M}–{first.ends_at:%H:%M} "
        f"-> {moved.starts_at:%H:%M}–{moved.ends_at:%H:%M}"
    )
    second = service.create_booking(Booking(
        boris, workplace, datetime(2026, 10, 12, 13), datetime(2026, 10, 12, 14)
    ))
    before = service.bookings()
    rejected_periods = (
        (
            "Нерабочее время",
            datetime(2026, 10, 12, 18), datetime(2026, 10, 12, 20),
        ),
        (
            "Конфликт с другой бронью",
            datetime(2026, 10, 12, 13, 30), datetime(2026, 10, 12, 14, 30),
        ),
    )
    for label, starts_at, ends_at in rejected_periods:
        try:
            service.reschedule(moved, starts_at, ends_at)
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
        assert service.bookings() == before
    assert service.bookings() == (moved, second)
    print("После отказов сохранено бронирований:", len(service.bookings()))


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

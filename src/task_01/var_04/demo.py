# Демонстрация

from datetime import datetime, timedelta
from decimal import Decimal

from main import RentalService
from models import Bicycle, Car, ElectricScooter, ReturnInfo, User


def scenario_01() -> None:
    print("\nСценарий 1: три вида транспорта и разные тарифы")
    user = User("Анна", 25, has_license=True)
    bicycle = Bicycle("B-1", "Городской велосипед")
    car = Car("C-1", "Седан")
    scooter = ElectricScooter("S-1", "Электросамокат")
    service = RentalService((bicycle, car, scooter))
    starts_at = datetime(2026, 10, 11, 10, 0)
    trips = (
        (bicycle, timedelta(minutes=90), ReturnInfo(), Decimal("180.00")),
        (car, timedelta(minutes=90), ReturnInfo(fuel_percent=40), Decimal("1000.00")),
        (
            scooter, timedelta(minutes=10, seconds=1),
            ReturnInfo(battery_percent=50), Decimal("160.00"),
        ),
    )
    for transport, duration, info, expected in trips:
        rental = service.rent(transport.transport_id, user, starts_at)
        assert not transport.is_available
        total = service.finish_rental(rental, starts_at + duration, info)
        assert total == expected == transport.calculate_cost(duration)
        assert rental.user is user and rental.ends_at == starts_at + duration
        assert rental.total == expected and transport.is_available
        print(f"{transport.name}: {duration}, стоимость {total:.2f}")


def scenario_02() -> None:
    print("\nСценарий 2: ограничения аренды и повторная выдача")
    car = Car("C-1", "Седан")
    scooter = ElectricScooter("S-1", "Электросамокат")
    service = RentalService((car, scooter))
    starts_at = datetime(2026, 10, 11, 12, 0)
    rejected_users = (
        (scooter, User("Илья", 15)),
        (car, User("Денис", 17, has_license=True)),
        (car, User("Мария", 25)),
    )
    for transport, user in rejected_users:
        try:
            service.rent(transport.transport_id, user, starts_at)
        except ValueError as error:
            print(f"{user.name}: {error}")
        else:
            raise AssertionError("Ожидался отказ в аренде")
        assert transport.is_available
    rental = service.rent(car.transport_id, User("Анна", 25, True), starts_at)
    try:
        service.rent(car.transport_id, User("Олег", 30, True), starts_at)
    except ValueError as error:
        print(f"Повторная выдача: {error}")
    else:
        raise AssertionError("Занятый автомобиль выдан повторно")
    assert rental.user.name == "Анна" and rental.ends_at is None
    assert not car.is_available
    ends_at = starts_at + timedelta(minutes=30)
    total = service.finish_rental(rental, ends_at, ReturnInfo(fuel_percent=20))
    assert total == Decimal("500.00")
    next_rental = service.rent(car.transport_id, User("Олег", 30, True), ends_at)
    assert next_rental is not rental and next_rental.user.name == "Олег"
    next_total = service.finish_rental(
        next_rental, ends_at + timedelta(minutes=30), ReturnInfo(fuel_percent=20)
    )
    assert next_total == Decimal("500.00")
    assert car.is_available and rental.total == Decimal("500.00")
    print("После возврата автомобиль выдан Олегу и снова возвращен")


def scenario_03() -> None:
    print("\nСценарий 3: условия возврата и сохранность аренды")
    car = Car("C-1", "Седан")
    scooter = ElectricScooter("S-1", "Электросамокат")
    service = RentalService((car, scooter))
    starts_at = datetime(2026, 10, 11, 14, 0)
    ends_at = starts_at + timedelta(minutes=10)
    user = User("Анна", 25, has_license=True)
    car_rental = service.rent(car.transport_id, user, starts_at)
    scooter_rental = service.rent(scooter.transport_id, user, starts_at)
    rejected_returns = (
        ("Топливо не указано", car_rental, ends_at, ReturnInfo()),
        ("Недостаточно топлива", car_rental, ends_at, ReturnInfo(fuel_percent=10)),
        (
            "Недостаточно заряда", scooter_rental, ends_at,
            ReturnInfo(battery_percent=10),
        ),
        (
            "Нулевая продолжительность", car_rental, starts_at,
            ReturnInfo(fuel_percent=20),
        ),
    )
    for label, rental, return_time, info in rejected_returns:
        try:
            service.finish_rental(rental, return_time, info)
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
        assert rental.ends_at is None and rental.total is None
        assert not rental.transport.is_available
    car_total = service.finish_rental(
        car_rental, ends_at, ReturnInfo(fuel_percent=20)
    )
    scooter_total = service.finish_rental(
        scooter_rental, ends_at, ReturnInfo(battery_percent=20)
    )
    assert car_total == Decimal("500.00")
    assert scooter_total == Decimal("150.00")
    try:
        service.finish_rental(car_rental, ends_at, ReturnInfo(fuel_percent=20))
    except ValueError as error:
        print(f"Повторный возврат: {error}")
    else:
        raise AssertionError("Аренда завершена повторно")
    assert car.is_available and scooter.is_available
    assert car_rental.total == Decimal("500.00")
    assert scooter_rental.total == Decimal("150.00")
    print(
        f"После исправления условий обе аренды завершены: "
        f"{car_total:.2f} и {scooter_total:.2f}"
    )


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

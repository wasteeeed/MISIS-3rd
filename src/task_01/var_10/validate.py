# Валидация


def validate_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} должен быть непустой строкой")


def validate_positive_quantity(quantity: int) -> None:
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Количество должно быть положительным целым числом")


def validate_stock_values(total: int, reserved: int) -> None:
    if type(total) is not int or type(reserved) is not int:
        raise ValueError("Остаток и резерв должны быть целыми числами")
    if total < 0 or reserved < 0 or reserved > total:
        raise ValueError("Остатки должны удовлетворять условию 0 <= резерв <= всего")


def validate_operation_type(operation: object, operation_type: type) -> None:
    if not isinstance(operation, operation_type):
        raise TypeError("Ожидается складская операция")


def validate_available_quantity(
    quantity: int, available: int, message: str
) -> None:
    validate_positive_quantity(quantity)
    if quantity > available:
        raise ValueError(message)


def validate_reservation(
    quantity: int, available: int, already_reserved: bool
) -> None:
    if already_reserved:
        raise ValueError("Товар уже зарезервирован для этого заказа")
    validate_available_quantity(quantity, available, "Недостаточно доступного товара")


def validate_active_reservation(exists: bool) -> None:
    if not exists:
        raise ValueError("Активный резерв не найден")


def validate_move_zones(from_zone_id: str, to_zone_id: str) -> None:
    validate_text(from_zone_id, "from_zone_id")
    validate_text(to_zone_id, "to_zone_id")
    if from_zone_id == to_zone_id:
        raise ValueError("Зоны перемещения должны различаться")


def validate_stock_state(
    zone_totals: dict[tuple[str, str], int],
    reservations: dict[tuple[str, str], tuple[tuple[str, int], ...]],
) -> None:
    for (product_id, zone_id), total in zone_totals.items():
        validate_text(product_id, "product_id")
        validate_text(zone_id, "zone_id")
        validate_stock_values(total, 0)

    reserved_by_zone: dict[tuple[str, str], int] = {}
    for (product_id, order_id), allocations in reservations.items():
        validate_text(product_id, "product_id")
        validate_text(order_id, "order_id")
        if not allocations:
            raise ValueError("Резерв должен содержать положительное количество товара")
        for zone_id, quantity in allocations:
            validate_text(zone_id, "zone_id")
            validate_positive_quantity(quantity)
            key = (product_id, zone_id)
            reserved_by_zone[key] = reserved_by_zone.get(key, 0) + quantity

    for key, reserved in reserved_by_zone.items():
        validate_stock_values(zone_totals.get(key, 0), reserved)

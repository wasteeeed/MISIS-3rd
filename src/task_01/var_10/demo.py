# Демонстрация

from main import Warehouse
from models import (
    CancelReservationOperation,
    ConfirmReservationOperation,
    MoveOperation,
    ReceiptOperation,
    ReserveOperation,
    Stock,
    WriteOffOperation,
)


def scenario_01() -> None:
    print("\nСценарий 1: резерв и отгрузка")
    warehouse = Warehouse()
    product_id = "SKU-1"
    operations = (
        ReceiptOperation(
            product_id=product_id, quantity=10, reason="Поставка"
        ),
        ReserveOperation(
            product_id=product_id, order_id="ORDER-1", quantity=4, reason="Заказ"
        ),
        ConfirmReservationOperation(
            product_id=product_id, order_id="ORDER-1", reason="Отгрузка"
        ),
    )
    expected_stocks = (Stock(10, 0), Stock(10, 4), Stock(6, 0))

    for operation, expected in zip(operations, expected_stocks, strict=True):
        warehouse.apply(operation)
        stock = warehouse.stock(product_id)
        assert stock == expected
        print(f"{operation.reason}: {stock}, доступно {stock.available}")

    assert warehouse.history() == operations
    print("История:", [operation.reason for operation in warehouse.history()])


def scenario_02() -> None:
    print("\nСценарий 2: отмена резерва, перемещение и списание")
    warehouse = Warehouse()
    product_id = "SKU-2"
    operations = (
        ReceiptOperation(
            product_id=product_id, zone_id="A", quantity=10, reason="Поставка в A"
        ),
        ReceiptOperation(
            product_id=product_id, zone_id="B", quantity=5, reason="Поставка в B"
        ),
        ReserveOperation(
            product_id=product_id, order_id="ORDER-2", quantity=12, reason="Заказ"
        ),
        CancelReservationOperation(
            product_id=product_id, order_id="ORDER-2", reason="Отмена заказа"
        ),
        MoveOperation(
            product_id=product_id, from_zone_id="A", to_zone_id="B",
            quantity=3, reason="Перемещение в B",
        ),
        WriteOffOperation(
            product_id=product_id, zone_id="B", quantity=1, reason="Списание"
        ),
    )

    for operation in operations:
        warehouse.apply(operation)

    assert warehouse.stock(product_id) == Stock(14, 0)
    assert warehouse.stock(product_id, "A") == Stock(7, 0)
    assert warehouse.stock(product_id, "B") == Stock(7, 0)
    assert warehouse.history() == operations
    print("Зона A:", warehouse.stock(product_id, "A"))
    print("Зона B:", warehouse.stock(product_id, "B"))
    print("Всего:", warehouse.stock(product_id))


def scenario_03() -> None:
    print("\nСценарий 3: отказы без изменения остатков и истории")
    warehouse = Warehouse()
    product_id = "SKU-3"
    warehouse.apply(ReceiptOperation(
        product_id=product_id, zone_id="A", quantity=5, reason="Поставка"
    ))
    warehouse.apply(ReserveOperation(
        product_id=product_id, order_id="ORDER-3", quantity=4, reason="Заказ"
    ))
    before_stock = warehouse.stock(product_id)
    before_history = warehouse.history()
    rejected_operations = (
        ReserveOperation(
            product_id=product_id, order_id="ORDER-4", quantity=2,
            reason="Резерв сверх доступного",
        ),
        MoveOperation(
            product_id=product_id, from_zone_id="A", to_zone_id="B",
            quantity=2, reason="Перемещение зарезервированного товара",
        ),
        WriteOffOperation(
            product_id=product_id, zone_id="A", quantity=2,
            reason="Списание зарезервированного товара",
        ),
        ConfirmReservationOperation(
            product_id=product_id, order_id="UNKNOWN", reason="Отгрузка без резерва"
        ),
    )

    for operation in rejected_operations:
        try:
            warehouse.apply(operation)
        except ValueError as error:
            print(f"{operation.reason}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {operation.reason}")
        assert warehouse.stock(product_id) == before_stock
        assert warehouse.history() == before_history

    stock = warehouse.stock(product_id)
    assert stock == Stock(5, 4)
    print(f"После отказов: {stock}, доступно {stock.available}")


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

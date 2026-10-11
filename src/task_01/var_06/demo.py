# Демонстрация

from decimal import Decimal

from main import Cart, OrderService
from models import (
    AmountDiscount,
    DeliveryOption,
    OrderStatus,
    Product,
    PromoCodeDiscount,
    QuantityDiscount,
)


def scenario_01() -> None:
    print("\nСценарий 1: корзина, расчёт стоимости и выполнение заказа")
    book = Product("P-1", "Книга", Decimal("500.00"))
    mouse = Product("P-2", "Мышь", Decimal("1000.00"))
    cart = Cart()
    cart.add(book)
    cart.add(book)
    cart.add(mouse)
    service = OrderService((AmountDiscount(Decimal("1500.00"), Decimal(10)),))
    order = service.create_order(cart, DeliveryOption("Курьер", Decimal("300.00")))
    assert len(order.items) == 2 and order.quantity == 3
    assert order.subtotal == Decimal("2000.00")
    assert order.discount == Decimal("200.00")
    assert order.total == Decimal("2100.00")
    for item in order.items:
        print(f"{item.product.name}: {item.quantity} шт., {item.subtotal:.2f}")
    print(f"Товары: {order.subtotal:.2f}; скидка: {order.discount:.2f}")
    print(f"Получение: {order.delivery.name}, {order.delivery.cost:.2f}")
    print(f"Итого: {order.total:.2f}")
    print("Состояние:", order.status.value)
    steps = (
        (order.submit, OrderStatus.AWAITING_PAYMENT),
        (order.pay, OrderStatus.PAID),
        (order.ship, OrderStatus.SHIPPED),
        (order.complete, OrderStatus.COMPLETED),
    )
    for action, expected in steps:
        action()
        assert order.status is expected
        print("Состояние:", order.status.value)


def scenario_02() -> None:
    print("\nСценарий 2: выбор скидки, изменение получения и отмена")
    product = Product("P-1", "Наушники", Decimal("1000.00"))
    cart = Cart()
    cart.add(product, 3)
    service = OrderService(
        (
            AmountDiscount(Decimal("2000.00"), Decimal(10)),
            PromoCodeDiscount("SAVE20", Decimal(20)),
            QuantityDiscount(3, Decimal(15)),
        )
    )
    order = service.create_order(
        cart, DeliveryOption("Курьер", Decimal("200.00")), "SAVE20"
    )
    assert order.discount == Decimal("600.00")
    assert order.total == Decimal("2600.00")
    print(f"Промокод: скидка {order.discount:.2f}, итог {order.total:.2f}")
    service.update_order(order, cart, DeliveryOption("Самовывоз"))
    assert order.discount == Decimal("450.00")
    assert order.total == Decimal("2550.00")
    print(
        f"Самовывоз без промокода: скидка {order.discount:.2f}, "
        f"итог {order.total:.2f}"
    )
    cart.add(product)
    assert cart.items()[0].quantity == 4
    assert order.quantity == 3 and order.total == Decimal("2550.00")
    print("Количество в корзине:", cart.items()[0].quantity)
    print("Количество в созданном заказе:", order.quantity)
    order.submit()
    order.cancel()
    assert order.status is OrderStatus.CANCELLED
    print("После отмены:", order.status.value)


def scenario_03() -> None:
    print("\nСценарий 3: недоступные товары и запреты после оплаты")
    service = OrderService()
    pickup = DeliveryOption("Самовывоз")
    unavailable = Cart()
    unavailable.add(Product("P-0", "Нет в продаже", Decimal("100.00"), False))
    for label, cart in (("Пустая корзина", Cart()), ("Недоступный товар", unavailable)):
        try:
            service.create_order(cart, pickup)
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
    cart = Cart()
    cart.add(Product("P-1", "Клавиатура", Decimal("2500.00")))
    order = service.create_order(cart, pickup)
    order.submit()
    order.pay()
    before = (order.status, order.items, order.delivery, order.discount, order.total)
    rejected_actions = (
        ("Повторная оплата", order.pay),
        ("Завершение без доставки", order.complete),
        ("Отмена после оплаты", order.cancel),
        ("Изменение после оплаты", lambda: service.update_order(order, cart, pickup)),
    )
    for label, action in rejected_actions:
        try:
            action()
        except ValueError as error:
            print(f"{label}: {error}")
        else:
            raise AssertionError(f"Ожидался отказ: {label}")
        assert (
            order.status, order.items, order.delivery, order.discount, order.total
        ) == before
    print(f"После отказов: {order.status.value}, итог {order.total:.2f}")


if __name__ == "__main__":
    scenario_01()
    scenario_02()
    scenario_03()

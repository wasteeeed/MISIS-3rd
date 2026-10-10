# Оформление заказа

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from models import DeliveryOption, DiscountRule, Order, OrderItem, Product, ZERO
from validate import (
    CENT,
    validate_discount_amount,
    validate_found,
    validate_positive_int,
    validate_same_product,
    validate_text,
    validate_type,
)


@dataclass(slots=True, eq=False, repr=False)
class Cart:
    __items: dict[str, OrderItem] = field(default_factory=dict, init=False)

    def add(self, product: Product, quantity: int = 1) -> None:
        validate_type(product, Product, "product")
        validate_positive_int(quantity, "quantity")
        existing = self.__items.get(product.product_id)
        validate_same_product(existing is None or existing.product == product)
        previous = existing.quantity if existing is not None else 0
        self.__items[product.product_id] = OrderItem(product, previous + quantity)

    def remove(self, product_id: str) -> None:
        validate_text(product_id, "product_id")
        validate_found(self.__items.get(product_id), "Товар не найден в корзине")
        del self.__items[product_id]

    def items(self) -> tuple[OrderItem, ...]:
        return tuple(self.__items.values())


@dataclass(frozen=True, slots=True)
class OrderService:
    discount_rules: tuple[DiscountRule, ...] = ()

    def __post_init__(self) -> None:
        rules = tuple(self.discount_rules)
        for rule in rules:
            validate_type(rule, DiscountRule, "discount_rule")
        object.__setattr__(self, "discount_rules", rules)

    def create_order(
        self, cart: Cart, delivery: DeliveryOption, promo_code: str | None = None
    ) -> Order:
        validate_type(cart, Cart, "cart")
        order = Order(cart.items(), delivery, promo_code)
        order._set_discount(self._calculate_discount(order))
        return order

    def update_order(
        self,
        order: Order,
        cart: Cart,
        delivery: DeliveryOption,
        promo_code: str | None = None,
    ) -> None:
        validate_type(order, Order, "order")
        order._ensure_editable()
        candidate = self.create_order(cart, delivery, promo_code)
        order._replace_contents(candidate)

    def _calculate_discount(self, order: Order) -> Decimal:
        subtotal, quantity = order.subtotal, order.quantity
        best = ZERO
        for rule in self.discount_rules:
            amount = rule.calculate(subtotal, quantity, order.promo_code)
            validate_discount_amount(amount, subtotal)
            best = max(best, amount)
        return best.quantize(CENT, rounding=ROUND_HALF_UP)

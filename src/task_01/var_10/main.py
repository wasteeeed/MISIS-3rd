# Управление складом

from copy import deepcopy
from dataclasses import dataclass, field

from models import Stock, StockOperation, StockState
from validate import validate_operation_type, validate_stock_state, validate_text


@dataclass(slots=True, eq=False, repr=False)
class Warehouse:
    __history: list[StockOperation] = field(default_factory=list, init=False)

    def apply(self, operation: StockOperation) -> None:
        validate_operation_type(operation, StockOperation)
        validate_text(operation.product_id, "product_id")
        validate_text(operation.reason, "reason")
        record = deepcopy(operation)
        state = self._calculate_state()
        operation.apply(state)
        validate_stock_state(state.zone_totals, state.reservations)
        self.__history.append(record)

    def stock(self, product_id: str, zone_id: str | None = None) -> Stock:
        validate_text(product_id, "product_id")
        if zone_id is not None:
            validate_text(zone_id, "zone_id")
        return self._calculate_state().stock(product_id, zone_id)

    def history(self) -> tuple[StockOperation, ...]:
        return tuple(deepcopy(self.__history))

    def _calculate_state(self) -> StockState:
        state = StockState()
        for operation in self.history():
            operation.apply(state)
        return state

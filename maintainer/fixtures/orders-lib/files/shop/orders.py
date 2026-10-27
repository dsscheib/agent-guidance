"""Order lifecycle: placed -> delivered, or placed -> cancelled."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


class OrderError(Exception):
    """Raised when an operation is not allowed in the order's current state."""


@dataclass
class Order:
    order_id: str
    total: Decimal
    status: str = "placed"
    delivered_at: Optional[datetime] = None
    history: list = field(default_factory=list)

    def deliver(self, when):
        if self.status != "placed":
            raise OrderError(f"cannot deliver an order that is {self.status}")
        self.status = "delivered"
        self.delivered_at = when
        self.history.append(("delivered", when))

    def cancel(self, when):
        if self.status != "placed":
            raise OrderError(f"cannot cancel an order that is {self.status}")
        self.status = "cancelled"
        self.history.append(("cancelled", when))

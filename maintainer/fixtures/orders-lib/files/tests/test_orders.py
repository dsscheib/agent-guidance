import unittest
from datetime import datetime
from decimal import Decimal

from shop.orders import Order, OrderError


class OrderTests(unittest.TestCase):
    def test_deliver_records_time(self):
        order = Order("o-1", Decimal("19.99"))
        when = datetime(2026, 1, 2, 3, 4)
        order.deliver(when)
        self.assertEqual((order.status, order.delivered_at), ("delivered", when))

    def test_cannot_cancel_delivered_order(self):
        order = Order("o-2", Decimal("5.00"))
        order.deliver(datetime(2026, 1, 2))
        with self.assertRaises(OrderError):
            order.cancel(datetime(2026, 1, 3))


if __name__ == "__main__":
    unittest.main()

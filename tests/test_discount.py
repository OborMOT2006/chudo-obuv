import unittest
from datetime import date
from decimal import Decimal
from controllers.discount import discounted_price, previous_month_bounds


class DiscountTests(unittest.TestCase):
    def test_previous_month_for_january(self):
        self.assertEqual(previous_month_bounds(date(2026, 1, 14)), (date(2025, 12, 1), date(2026, 1, 1)))

    def test_previous_month_for_october(self):
        self.assertEqual(previous_month_bounds(date(2026, 10, 14)), (date(2026, 9, 1), date(2026, 10, 1)))

    def test_discount(self):
        self.assertEqual(discounted_price(2190, False), (Decimal('1642.50'), 25))
        self.assertEqual(discounted_price(2190, True), (Decimal('2190.00'), 0))

    def test_rounding(self):
        self.assertEqual(discounted_price('100.01', False), (Decimal('75.01'), 25))


if __name__ == '__main__':
    unittest.main()

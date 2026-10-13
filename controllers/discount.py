"""Правило КИМ: 25% при отсутствии заказов за предыдущий календарный месяц."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP


def previous_month_bounds(today=None):
    today = today or date.today()
    end = today.replace(day=1)
    start = (end - timedelta(days=1)).replace(day=1)
    return start, end


def discounted_price(price, ordered_last_month):
    price = Decimal(str(price))
    if ordered_last_month:
        return price.quantize(Decimal('0.01')), 0
    return (price * Decimal('0.75')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 25

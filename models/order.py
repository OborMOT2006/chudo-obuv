"""Транзакционное оформление и редактирование заказов с пересчётом остатков."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from db.connection import fetch_all, fetch_one, transaction
from controllers.discount import discounted_price, previous_month_bounds


def list_orders():
    return fetch_all('''
        SELECT o.order_id, o.order_date, o.user_id,
               TRIM(u.last_name || ' ' || u.first_name || ' ' || COALESCE(u.middle_name, '')) AS full_name,
               COALESCE(SUM(oi.quantity * oi.price), 0) AS total
        FROM orders o JOIN users u ON u.user_id = o.user_id
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, u.user_id
        ORDER BY o.order_date DESC, o.order_id DESC
    ''')


def get_order(order_id):
    order = fetch_one('''
        SELECT o.order_id, o.order_date, o.user_id,
               TRIM(u.last_name || ' ' || u.first_name || ' ' || COALESCE(u.middle_name, '')) AS full_name
        FROM orders o JOIN users u ON u.user_id = o.user_id WHERE o.order_id = %s
    ''', (order_id,))
    if not order:
        return None
    order['items'] = fetch_all('''
        SELECT oi.order_item_id, oi.quantity, oi.price, p.product_name, m.manufacturer_name,
               sz.size_value, oi.stock_item_id
        FROM order_items oi JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
        JOIN products p ON p.product_id = si.product_id
        JOIN manufacturers m ON m.manufacturer_id = p.manufacturer_id
        JOIN sizes sz ON sz.size_id = si.size_id
        WHERE oi.order_id = %s ORDER BY oi.order_item_id
    ''', (order_id,))
    order['total'] = sum((i['price'] * i['quantity'] for i in order['items']), Decimal('0'))
    return order


def create_order(user_id, items):
    """Блокировка склада FOR UPDATE защищает от продажи большего остатка."""
    if not items:
        raise ValueError('Нельзя оформить пустой заказ.')
    amounts = defaultdict(int)
    for item in items:
        stock_id, qty = int(item['stock_item_id']), int(item['quantity'])
        if stock_id <= 0 or qty <= 0:
            raise ValueError('Количество должно быть положительным целым числом.')
        amounts[stock_id] += qty
    start, end = previous_month_bounds()
    with transaction() as cur:
        cur.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
        if not cur.fetchone():
            raise ValueError('Пользователь не найден.')
        verified = []
        # Сортировка ID исключает взаимоблокировку при параллельных заказах.
        for stock_id, qty in sorted(amounts.items()):
            cur.execute('''
                SELECT si.quantity_available, p.product_id, p.price FROM stock_items si
                JOIN products p ON p.product_id = si.product_id
                WHERE si.stock_item_id = %s FOR UPDATE OF si
            ''', (stock_id,))
            row = cur.fetchone()
            if row is None or row[0] < qty:
                raise ValueError('Недостаточно товара. Обновите каталог и проверьте количество.')
            cur.execute('''
                SELECT EXISTS (SELECT 1 FROM order_items oi
                    JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
                    JOIN orders o ON o.order_id = oi.order_id
                    WHERE si.product_id = %s AND o.order_date >= %s AND o.order_date < %s)
            ''', (row[1], start, end))
            was_ordered = cur.fetchone()[0]
            price, _ = discounted_price(row[2], was_ordered)
            verified.append((stock_id, qty, price))
        cur.execute('INSERT INTO orders (order_date, user_id) VALUES (CURRENT_DATE, %s) RETURNING order_id', (user_id,))
        order_id = cur.fetchone()[0]
        for stock_id, qty, price in verified:
            cur.execute('UPDATE stock_items SET quantity_available = quantity_available - %s WHERE stock_item_id = %s', (qty, stock_id))
            cur.execute('''
                INSERT INTO order_items (order_id, stock_item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, stock_id, qty, price))
    return order_id


def delete_order(order_id):
    with transaction() as cur:
        cur.execute('SELECT order_id FROM orders WHERE order_id = %s FOR UPDATE', (order_id,))
        if not cur.fetchone():
            raise ValueError('Заказ не найден.')
        cur.execute('SELECT stock_item_id, quantity FROM order_items WHERE order_id = %s', (order_id,))
        for stock_id, qty in cur.fetchall():
            cur.execute('UPDATE stock_items SET quantity_available = quantity_available + %s WHERE stock_item_id = %s', (qty, stock_id))
        cur.execute('DELETE FROM orders WHERE order_id = %s', (order_id,))


def update_order(order_id, new_date, remove_item_ids):
    """Редактирование даты и удаление позиций (только из указанного заказа)."""
    removed = list(dict.fromkeys(int(i) for i in remove_item_ids))
    with transaction() as cur:
        cur.execute('SELECT order_id FROM orders WHERE order_id = %s FOR UPDATE', (order_id,))
        if not cur.fetchone():
            raise ValueError('Заказ не найден.')
        cur.execute('UPDATE orders SET order_date = %s WHERE order_id = %s', (new_date, order_id))
        for item_id in removed:
            cur.execute('''
                DELETE FROM order_items WHERE order_item_id = %s AND order_id = %s
                RETURNING stock_item_id, quantity
            ''', (item_id, order_id))
            item = cur.fetchone()
            if item is None:
                raise ValueError('Позиция заказа не найдена.')
            cur.execute('''
                UPDATE stock_items SET quantity_available = quantity_available + %s
                WHERE stock_item_id = %s
            ''', (item[1], item[0]))

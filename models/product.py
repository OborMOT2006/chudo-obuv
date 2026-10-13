"""Каталог, поиск/фильтрация и актуальные размеры."""
from datetime import date
from db.connection import fetch_all, fetch_one
from controllers.discount import discounted_price, previous_month_bounds

BASE_QUERY = '''
    SELECT p.product_id, p.product_name, p.subcategory, p.image_path,
           p.description, p.composition, p.price,
           c.category_id, c.category_name, m.manufacturer_name,
           COALESCE(SUM(si.quantity_available),0)::INTEGER AS total_quantity,
           EXISTS (
               SELECT 1 FROM order_items oi
               JOIN stock_items soi ON soi.stock_item_id = oi.stock_item_id
               JOIN orders o ON o.order_id = oi.order_id
               WHERE soi.product_id = p.product_id AND o.order_date >= %s AND o.order_date < %s
           ) AS ordered_last_month
    FROM products p
    JOIN categories c ON c.category_id = p.category_id
    JOIN manufacturers m ON m.manufacturer_id = p.manufacturer_id
    LEFT JOIN stock_items si ON si.product_id = p.product_id
'''
GROUP_QUERY = '''GROUP BY p.product_id, c.category_id, m.manufacturer_id'''


def _finalize(p):
    final_price, discount = discounted_price(p['price'], p['ordered_last_month'])
    p['final_price'] = final_price
    p['discount_percent'] = discount
    p['is_low_stock'] = p['total_quantity'] <= 3
    return p


def list_products(category_id=None, search='', sort=''):
    start, end = previous_month_bounds()
    conditions = []
    params = [start, end]
    if category_id:
        conditions.append('c.category_id = %s')
        params.append(category_id)
    if search.strip():
        conditions.append("(p.product_name ILIKE %s OR COALESCE(p.description, '') ILIKE %s)")
        term = '%' + search.strip() + '%'
        params.extend([term, term])
    where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
    products = [_finalize(p) for p in fetch_all(BASE_QUERY + where + GROUP_QUERY + ' ORDER BY p.product_id', params)]
    if sort in ('price_asc', 'price_desc'):
        products.sort(key=lambda p: (p['final_price'], p['product_id']), reverse=(sort == 'price_desc'))
    return products


def get_product(product_id):
    start, end = previous_month_bounds()
    p = fetch_one(BASE_QUERY + ' WHERE p.product_id = %s ' + GROUP_QUERY, (start, end, product_id))
    return _finalize(p) if p else None


def get_sizes_for_product(product_id):
    return fetch_all('''
        SELECT si.stock_item_id, sz.size_value, si.quantity_available
        FROM stock_items si JOIN sizes sz ON sz.size_id = si.size_id
        WHERE si.product_id = %s ORDER BY sz.size_value
    ''', (product_id,))


def list_categories():
    return fetch_all('SELECT category_id, category_name FROM categories ORDER BY category_name')

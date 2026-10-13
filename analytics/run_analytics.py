"""Модуль 5: шесть задач аналитики по CSV из Приложения 4.

Использование: python analytics/run_analytics.py /путь/к/папке/CSV
CSV к этой версии КИМ не приложены. По умолчанию используются распространённые
названия колонок; под фактическую структуру файла их можно поправить здесь.
"""
import sys
from pathlib import Path
import pandas as pd

START = pd.Timestamp('2026-01-01')
END = pd.Timestamp('2026-04-01')


def read_csv(folder, filename):
    path = folder / filename
    if not path.exists():
        raise FileNotFoundError('Не найден файл: ' + str(path))
    try:
        df = pd.read_csv(path, sep=None, engine='python', encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep=None, engine='python', encoding='cp1251')
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def rename(df, aliases):
    """Приводит варианты названий колонок к одному виду."""
    actual = {}
    for canonical, variants in aliases.items():
        for v in [canonical] + variants:
            if v in df.columns:
                actual[v] = canonical
                break
    return df.rename(columns=actual)


def require(df, cols, source):
    absent = set(cols) - set(df.columns)
    if absent:
        raise ValueError('{}: не найдены колонки {}. Есть: {}'.format(source, ', '.join(sorted(absent)), ', '.join(df.columns)))


def prepared(folder):
    s = rename(read_csv(folder, 'Sessions_analytics.csv'), {
        'session_id': ['id'], 'user_id': ['client_id', 'customer_id'],
        'started_at': ['start_time', 'session_start', 'session_start_at', 'session_date', 'created_at', 'start_at'],
        'device_type': ['device'], 'traffic_source': ['source', 'channel']})
    o = rename(read_csv(folder, 'Orders_analytics.csv'), {
        'order_id': ['id'], 'user_id': ['client_id', 'customer_id'],
        'session_id': ['session'], 'created_at': ['order_date', 'ordered_at', 'order_datetime', 'created_date'],
        'status': ['order_status']})
    oi = rename(read_csv(folder, 'Order_items_analytics.csv'), {
        'order_id': ['id_order'], 'model_id': ['shoe_model_id', 'product_id'],
        'quantity': ['qty'], 'discount_percent': ['discount', 'discount_pct'],
        'unit_price': ['price', 'price_per_unit', 'sale_price'], 'line_total': ['total_price', 'subtotal']})
    m = rename(read_csv(folder, 'Shoe_models_analytics.csv'), {
        'model_id': ['shoe_model_id', 'product_id', 'id'], 'category': ['category_name']})
    require(s, ['session_id', 'user_id', 'started_at', 'device_type', 'traffic_source'], 'Sessions')
    require(o, ['order_id', 'user_id', 'session_id', 'created_at', 'status'], 'Orders')
    require(oi, ['order_id', 'model_id', 'quantity', 'discount_percent'], 'Order_items')
    require(m, ['model_id', 'category'], 'Shoe_models')
    s['started_at'] = pd.to_datetime(s['started_at'], errors='coerce')
    o['created_at'] = pd.to_datetime(o['created_at'], errors='coerce')
    s = s[s['started_at'].notna() & (s['started_at'] >= START) & (s['started_at'] < END)].copy()
    o = o[o['created_at'].notna() & (o['created_at'] >= START) & (o['created_at'] < END) &
          (o['status'].astype(str).str.lower().isin(['completed', 'завершён', 'завершен']))].copy()
    oi['quantity'] = pd.to_numeric(oi['quantity'], errors='raise')
    oi['discount_percent'] = pd.to_numeric(oi['discount_percent'], errors='raise')
    return s, o, oi[oi['order_id'].isin(o['order_id'])].copy(), m


def calculate(folder):
    s, o, oi, m = prepared(folder)
    # 5.1: конверсия уникальных посетителей по устройству их сессии покупки.
    visitors = s.groupby('device_type')['user_id'].nunique()
    buyers = o.merge(s[['session_id', 'device_type']], on='session_id', how='inner')
    buyers = buyers.groupby('device_type')['user_id'].nunique()
    conversion = buyers.div(visitors).fillna(0)
    print('5.1 Максимальная конверсия:', conversion.idxmax(), '(по устройствам:', conversion.to_dict(), ')')

    # 5.2: первая сессия пользователя -> первый завершённый заказ (до 7 суток).
    first_visit = s.groupby('user_id')['started_at'].min()
    first_buy = o.groupby('user_id')['created_at'].min()
    durations = (first_buy - first_visit).dt.total_seconds().div(60).dropna()
    durations = durations[(durations >= 0) & (durations <= 7 * 24 * 60)]
    print('5.2 Медиана, минут:', durations.median() if len(durations) else 'нет данных')

    # 5.3: пользователи с первой сессией в январе, вернувшиеся в феврале.
    first_rows = s.sort_values('started_at').drop_duplicates('user_id')
    january = first_rows[(first_rows['started_at'] >= pd.Timestamp('2026-01-01')) &
                         (first_rows['started_at'] < pd.Timestamp('2026-02-01'))]
    feb_users = set(s.loc[(s['started_at'] >= pd.Timestamp('2026-02-01')) &
                         (s['started_at'] < pd.Timestamp('2026-03-01')), 'user_id'])
    rate = january.assign(returned=january['user_id'].isin(feb_users)).groupby('traffic_source')['returned'].mean()
    print('5.3 Наибольшее удержание:', rate.idxmax() if len(rate) else 'нет данных', rate.to_dict())

    # 5.4: стоимость заказа как сумма стоимостей позиций.
    if 'line_total' in oi:
        lines = pd.to_numeric(oi['line_total'])
    elif 'unit_price' in oi:
        # По задаче стоимость позиции может уже быть с учётом скидки; проверьте CSV.
        lines = pd.to_numeric(oi['unit_price']) * oi['quantity']
    else:
        raise ValueError('5.4: требуется unit_price/price либо line_total/subtotal в Order_items CSV')
    totals = oi.assign(line_value=lines).groupby('order_id')['line_value'].sum()
    q1, q3 = totals.quantile(.25), totals.quantile(.75)
    iqr = q3 - q1
    kept = totals[(totals >= q1 - 1.5 * iqr) & (totals <= q3 + 1.5 * iqr)]
    print('5.4 Осталось заказов после IQR:', len(kept))

    # 5.5: корреляция Пирсона по позициям завершённых заказов.
    coeff = oi['discount_percent'].corr(oi['quantity'], method='pearson')
    print('5.5 Корреляция:', '{:.3f}'.format(coeff))

    # 5.6: количество пар по категории, а не количество заказов.
    joined = oi.merge(m[['model_id', 'category']], on='model_id')
    qty = joined.groupby('category')['quantity'].sum()
    print('5.6 Категория-лидер:', qty.idxmax() if len(qty) else 'нет данных', qty.to_dict())


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Запуск: python analytics/run_analytics.py /путь/к/папке/с_CSV')
        sys.exit(1)
    try:
        calculate(Path(sys.argv[1]))
    except (ValueError, FileNotFoundError, KeyError) as error:
        print('Ошибка исходных данных:', error)
        sys.exit(2)

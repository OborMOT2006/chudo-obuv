"""Сборка db/data.sql из пяти исходных Excel. Интернет/СУБД не требуются."""
from collections import OrderedDict
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUTPUT = ROOT / 'db' / 'data.sql'


def rows(name):
    wb = openpyxl.load_workbook(DATA / (name + '_import.xlsx'), read_only=True, data_only=True)
    return list(wb.active.values)[1:]


def quote(v):
    if v is None:
        return 'NULL'
    if isinstance(v, (datetime, date)):
        v = v.strftime('%Y-%m-%d')
    if isinstance(v, (int, float, Decimal)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def main():
    products_x = rows('Products')
    sizes_x = rows('Sizes')
    stock_x = rows('Stock_Items')
    orders_x = rows('Orders')
    users_x = rows('Users')
    pmap = OrderedDict(((r[3],r[4]),r) for r in products_x)
    # В исходном Products отсутствуют три модели, но они есть в Stock и Orders.
    # Восстанавливаем только известные атрибуты и явно оставляем неизвестные пустыми.
    for name, manufacturer, size, quantity in stock_x:
        if (name,manufacturer) not in pmap:
            order_match = next((r for r in orders_x if r[4]==name and r[5]==manufacturer),None)
            cat = order_match[3] if order_match else 'Не указана'
            price = order_match[8] if order_match else 0
            pmap[(name,manufacturer)] = (cat, None, None, name, manufacturer, None, None, price)
    roles = list(OrderedDict((r[4], None) for r in users_x))
    categories = list(OrderedDict((str(r[0]),None) for r in pmap.values()))
    manufacturers = list(OrderedDict((str(r[4]),None) for r in pmap.values()))
    sizes = list(OrderedDict((Decimal(str(r[0])),None) for r in sizes_x))
    rids={v:i+1 for i,v in enumerate(roles)}
    cids={v:i+1 for i,v in enumerate(categories)}
    mids={v:i+1 for i,v in enumerate(manufacturers)}
    sids={v:i+1 for i,v in enumerate(sizes)}
    pids={v:i+1 for i,v in enumerate(pmap)}
    uid={r[3]:i+1 for i,r in enumerate(users_x)}
    full_names={ ' '.join(str(t or '').strip() for t in r[:3]).strip(): uid[r[3]] for r in users_x }
    # Если в исходных заказах есть ФИО, отсутствующее среди Users, не игнорируем его.
    unmatched={r[2] for r in orders_x}-set(full_names)
    if unmatched:
        raise ValueError('ФИО заказов отсутствуют в Users_import: '+str(unmatched))
    commands=['-- Сгенерировано scripts/build_data_sql.py. Исходные данные в data/*.xlsx.',
              '-- Запускать ОДИН раз после db/schema.sql. Не вычитать исторические заказы из остатков.',
              'BEGIN;']
    def insert(table, fields, values):
        commands.append('INSERT INTO '+table+' ('+', '.join(fields)+') VALUES ('+', '.join(quote(v) for v in values)+');')
    for x, r in enumerate(roles,1): insert('roles', ['role_id','role_name'], [x,r])
    for x, c in enumerate(categories,1): insert('categories',['category_id','category_name'],[x,c])
    for x, m in enumerate(manufacturers,1): insert('manufacturers',['manufacturer_id','manufacturer_name'],[x,m])
    for r in users_x:
        i=uid[r[3]]
        insert('users',['user_id','last_name','first_name','middle_name','login','role_id'], [i,*r[:4],rids[r[4]]])
    for x,size in enumerate(sizes,1): insert('sizes',['size_id','size_value'],[x,size])
    for (name,manufacturer),r in pmap.items():
        insert('products',['product_id','category_id','manufacturer_id','subcategory','product_name','image_path','description','composition','price'],
               [pids[(name,manufacturer)],cids[str(r[0])],mids[str(manufacturer)],r[1],name,r[2],r[5],r[6],r[7]])
    stock_id={}
    for x,(name,manufacturer,size,quantity) in enumerate(stock_x,1):
        key=(name,manufacturer,Decimal(str(size)))
        if key in stock_id: raise ValueError('Дублирующаяся складская позиция '+str(key))
        stock_id[key]=x
        insert('stock_items',['stock_item_id','product_id','size_id','quantity_available'],[x,pids[(name,manufacturer)],sids[Decimal(str(size))],int(quantity)])
    orders = OrderedDict()
    for r in orders_x:
        n=int(r[0])
        if n not in orders: orders[n]=(r[1],r[2])
        elif orders[n] != (r[1],r[2]): raise ValueError('Разные дата/клиент одного заказа')
    for n, (d,fio) in orders.items(): insert('orders',['order_id','order_date','user_id'],[n,d,full_names[fio]])
    for x,r in enumerate(orders_x,1):
        key=(r[4],r[5],Decimal(str(r[6])))
        insert('order_items',['order_item_id','order_id','stock_item_id','quantity','price'],[x,int(r[0]),stock_id[key],int(r[7]),r[8]])
    counters={'roles':len(roles),'categories':len(categories),'manufacturers':len(manufacturers),
              'users':len(uid),'sizes':len(sizes),'products':len(pids),'stock_items':len(stock_x),
              'orders':max(orders),'order_items':len(orders_x)}
    for table,last in counters.items():
        commands.append("SELECT setval(pg_get_serial_sequence('"+table+"', '"+({'categories':'category_id','manufacturers':'manufacturer_id','roles':'role_id','users':'user_id','sizes':'size_id','products':'product_id','stock_items':'stock_item_id','orders':'order_id','order_items':'order_item_id'}[table])+"'), "+str(last)+", true);")
    commands.append('COMMIT;')
    OUTPUT.write_text('\n'.join(commands)+'\n',encoding='utf-8')
    print('Создан',OUTPUT.name, '—',len(pids),'моделей,',len(stock_x),'складских позиций,',len(orders),'заказов,',len(orders_x),'строк заказов')

if __name__=='__main__': main()

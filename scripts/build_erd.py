"""Создание ERD_module_1.pdf через Graphviz (dot)."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DOCS.mkdir(exist_ok=True)

TABLES = {
 'roles': [('role_id','SERIAL','PK'),('role_name','VARCHAR(70)','UQ')],
 'users': [('user_id','SERIAL','PK'),('last_name','VARCHAR(100)',''),('first_name','VARCHAR(100)',''),('middle_name','VARCHAR(100)',''),('login','VARCHAR(100)','UQ'),('role_id','INTEGER','FK')],
 'categories':[('category_id','SERIAL','PK'),('category_name','VARCHAR(150)','UQ')],
 'manufacturers':[('manufacturer_id','SERIAL','PK'),('manufacturer_name','VARCHAR(200)','UQ')],
 'products':[('product_id','SERIAL','PK'),('category_id','INTEGER','FK'),('manufacturer_id','INTEGER','FK'),('subcategory','VARCHAR(150)',''),('product_name','VARCHAR(255)',''),('image_path','VARCHAR(255)',''),('description','TEXT',''),('composition','TEXT',''),('price','NUMERIC(12,2)','')],
 'sizes':[('size_id','SERIAL','PK'),('size_value','NUMERIC(4,1)','UQ')],
 'stock_items':[('stock_item_id','SERIAL','PK'),('product_id','INTEGER','FK'),('size_id','INTEGER','FK'),('quantity_available','INTEGER','')],
 'orders':[('order_id','SERIAL','PK'),('order_date','DATE',''),('user_id','INTEGER','FK')],
 'order_items':[('order_item_id','SERIAL','PK'),('order_id','INTEGER','FK'),('stock_item_id','INTEGER','FK'),('quantity','INTEGER',''),('price','NUMERIC(12,2)','')],
}
EDGES=[('users','roles','role_id'),('products','categories','category_id'),('products','manufacturers','manufacturer_id'),('stock_items','products','product_id'),('stock_items','sizes','size_id'),('orders','users','user_id'),('order_items','orders','order_id'),('order_items','stock_items','stock_item_id')]


def node(name, fields):
    rows=['<TR><TD COLSPAN="3" BGCOLOR="#D2F6E7" ALIGN="LEFT"><FONT POINT-SIZE="15"><B>'+name+'</B></FONT></TD></TR>']
    for i,(field,typ,key) in enumerate(fields):
        bg=' BGCOLOR="#F2FAF7"' if i%2==0 else ''
        rows.append('<TR><TD ALIGN="LEFT"'+bg+'><B>'+field+'</B></TD><TD ALIGN="LEFT"'+bg+'>'+typ.replace('<','&lt;')+'</TD><TD ALIGN="CENTER"'+bg+'><FONT COLOR="#3E827E">'+(key or '-')+'</FONT></TD></TR>')
    return name+' [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" COLOR="#70B2AF">'+''.join(rows)+'</TABLE>>];'


def main():
    dot=['digraph ERD {', 'graph [rankdir=LR, bgcolor="white", splines=polyline, nodesep=0.45, ranksep=1.0, pad=0.4];',
         'node [shape=plaintext, fontname="DejaVu Sans", fontsize=10];',
         'edge [color="#528F8A", arrowsize=0.7, penwidth=1.6, fontname="DejaVu Sans", fontsize=9];']
    for name,fields in TABLES.items(): dot.append(node(name,fields))
    for source,target,column in EDGES:
        dot.append(source+' -> '+target+' [label="'+column+'", arrowhead=vee];')
    dot.append('}')
    path=DOCS/'ERD_module_1.dot'
    path.write_text('\n'.join(dot)+'\n',encoding='utf-8')
    subprocess.run(['dot','-Tpdf',str(path),'-o',str(DOCS/'ERD_module_1.pdf')],check=True)
    print('ERD сгенерирована')

if __name__ == '__main__': main()

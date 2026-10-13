"""Окна интерфейса «Чудо Обувь», PyQt5 / Python 3.8+."""
from decimal import Decimal
from pathlib import Path

from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QComboBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget,
    QDateEdit, QInputDialog, QFrame, QMessageBox,
)

from controllers import auth_controller
from models import product as products
from models import order as orders
from models import user as users
from utils import messages

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / 'resources' / 'images'


def money(value):
    return '{:,.2f} ₽'.format(Decimal(str(value))).replace(',', ' ')


def image_label(file_name, width, height):
    label = QLabel()
    label.setFixedSize(width, height)
    label.setAlignment(Qt.AlignCenter)
    image_path = IMAGES / (file_name or 'picture.png')
    if not image_path.is_file():
        image_path = IMAGES / 'picture.png'
    pixmap = QPixmap(str(image_path))
    if not pixmap.isNull():
        label.setPixmap(pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return label


def label(text, bold=False):
    widget = QLabel(str(text))
    widget.setWordWrap(True)
    if bold:
        font = widget.font()
        font.setBold(True)
        widget.setFont(font)
    return widget


class LoginWindow(QWidget):
    """Гость или вход по логину, без пароля — так требует КИМ."""
    entered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Чудо Обувь — Вход')
        self.setWindowIcon(QIcon(str(IMAGES / 'icon.ico')))
        self.setFixedSize(440, 405)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 24)
        layout.addWidget(image_label('logo.png', 175, 105), alignment=Qt.AlignHCenter)
        heading = label('Чудо Обувь', True)
        heading.setAlignment(Qt.AlignCenter)
        heading.setObjectName('windowTitle')
        layout.addWidget(heading)
        layout.addWidget(label('Вход по логину (пароль не требуется)'))
        self.login = QLineEdit()
        self.login.setPlaceholderText('Например: isivanov')
        self.login.returnPressed.connect(self.sign_in)
        layout.addWidget(self.login)
        btn = QPushButton('Войти')
        btn.clicked.connect(self.sign_in)
        layout.addWidget(btn)
        guest_btn = QPushButton('Продолжить без входа — каталог')
        guest_btn.setObjectName('secondaryButton')
        guest_btn.clicked.connect(self.enter_guest)
        layout.addWidget(guest_btn)
        layout.addWidget(label('Администратор: isivanov · Менеджер: papetrov · Клиент: asidorova'))

    def sign_in(self):
        if not self.login.text().strip():
            messages.show_warning(self, 'Введите логин пользователя.')
            return
        try:
            ok, error = auth_controller.login(self.login.text())
        except Exception as exc:
            messages.show_error(self, 'Ошибка базы данных: {}. Проверьте подключение.'.format(exc))
            return
        if not ok:
            messages.show_error(self, error + ' Проверьте написание логина.')
            return
        self.entered.emit()

    def enter_guest(self):
        auth_controller.guest()
        self.entered.emit()


class ProductDialog(QDialog):
    """Карточка товара с выбором существующего размера и количества."""
    added = pyqtSignal(object)

    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product = products.get_product(product_id)
        if not self.product:
            raise ValueError('Товар не найден.')
        self.sizes = products.get_sizes_for_product(product_id)
        self.setWindowTitle('Чудо Обувь — Карточка товара')
        self.resize(730, 530)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(image_label(self.product['image_path'], 230, 210))
        details = QVBoxLayout()
        for key, val in [
            ('', '{} | {}'.format(self.product['manufacturer_name'], self.product['product_name'])),
            ('Категория', self.product['category_name']),
            ('Подкатегория', self.product['subcategory'] or '—'),
            ('Цена со скидкой', money(self.product['final_price'])),
            ('Скидка', str(self.product['discount_percent']) + '%'),
            ('Состав', self.product['composition'] or 'Нет данных'),
            ('Описание', self.product['description'] or 'Нет данных'),
        ]:
            details.addWidget(label((key + ': ' if key else '') + str(val), not bool(key)))
        details.addStretch()
        top.addLayout(details, 1)
        layout.addLayout(top)
        layout.addWidget(label('Доступные размеры и количество:'))
        form = QHBoxLayout()
        self.size_combo = QComboBox()
        for size in self.sizes:
            if size['quantity_available'] > 0:
                self.size_combo.addItem('{} — {} пар'.format(size['size_value'], size['quantity_available']), size)
        self.size_combo.currentIndexChanged.connect(self.size_changed)
        form.addWidget(self.size_combo, 3)
        form.addWidget(label('Количество'))
        self.qty = QSpinBox()
        self.qty.setMinimum(1)
        form.addWidget(self.qty)
        layout.addLayout(form)
        self.add_btn = QPushButton('Добавить в корзину')
        self.add_btn.clicked.connect(self.add_product)
        layout.addWidget(self.add_btn)
        back = QPushButton('Назад')
        back.setObjectName('secondaryButton')
        back.clicked.connect(self.reject)
        layout.addWidget(back)
        if not auth_controller.current_user():
            self.add_btn.setEnabled(False)
            self.add_btn.setText('Для заказа войдите по логину')
        self.size_changed()

    def size_changed(self, *_):
        row = self.size_combo.currentData()
        enabled = bool(row) and auth_controller.current_user() is not None
        self.add_btn.setEnabled(enabled)
        if row:
            self.qty.setMaximum(row['quantity_available'])
            self.qty.setValue(1)

    def add_product(self):
        row = self.size_combo.currentData()
        if not row:
            messages.show_warning(self, 'Выберите доступный размер.')
            return
        self.added.emit({
            'stock_item_id': row['stock_item_id'],
            'quantity': self.qty.value(),
            'product_id': self.product['product_id'],
            'name': self.product['product_name'],
            'manufacturer': self.product['manufacturer_name'],
            'size': str(row['size_value']),
            'price': self.product['final_price'],
            'available': row['quantity_available'],
        })
        self.accept()


class CartDialog(QDialog):
    """Редактируемая корзина; запись в БД происходит только по подтверждению."""
    placed = pyqtSignal()

    def __init__(self, cart, customer_user_id, parent=None):
        super().__init__(parent)
        self.cart = cart
        self.customer_user_id = customer_user_id
        self.setWindowTitle('Чудо Обувь — Корзина')
        self.resize(830, 530)
        layout = QVBoxLayout(self)
        layout.addWidget(label('Проверьте товары и количество перед оформлением', True))
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['Модель', 'Размер', 'Цена', 'Количество', 'Сумма', 'Удалить'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.total_label = label('')
        layout.addWidget(self.total_label)
        row = QHBoxLayout()
        back = QPushButton('Назад — продолжить выбор')
        back.setObjectName('secondaryButton')
        back.clicked.connect(self.reject)
        row.addWidget(back)
        cancel = QPushButton('Очистить корзину')
        cancel.setObjectName('secondaryButton')
        cancel.clicked.connect(self.clear_cart)
        row.addWidget(cancel)
        confirm = QPushButton('Подтвердить заказ')
        confirm.clicked.connect(self.confirm)
        row.addWidget(confirm)
        layout.addLayout(row)
        self.render()

    def render(self):
        self.table.setRowCount(0)
        total = Decimal('0')
        for item in self.cart:
            index = self.table.rowCount()
            self.table.insertRow(index)
            for col, content in [(0, item['manufacturer'] + ' | ' + item['name']),
                                 (1, item['size']), (2, money(item['price']))]:
                self.table.setItem(index, col, QTableWidgetItem(content))
            qty = QSpinBox()
            qty.setRange(1, max(item['available'], item['quantity']))
            qty.setValue(item['quantity'])
            qty.valueChanged.connect(lambda value, ref=item: self.update_qty(ref, value))
            self.table.setCellWidget(index, 3, qty)
            self.table.setItem(index, 4, QTableWidgetItem(money(item['price'] * item['quantity'])))
            remove = QPushButton('Убрать')
            remove.setObjectName('secondaryButton')
            remove.clicked.connect(lambda _, ref=item: self.remove_item(ref))
            self.table.setCellWidget(index, 5, remove)
            total += item['price'] * item['quantity']
        self.total_label.setText('Всего: ' + money(total))

    def update_qty(self, item, new_qty):
        item['quantity'] = new_qty
        index = self.cart.index(item)
        self.table.item(index, 4).setText(money(item['price'] * new_qty))
        total = sum((it['price'] * it['quantity'] for it in self.cart), Decimal('0'))
        self.total_label.setText('Всего: ' + money(total))

    def remove_item(self, item):
        self.cart.remove(item)
        self.render()

    def clear_cart(self):
        if messages.ask_confirmation(self, 'Очистить корзину без оформления?'):
            self.cart.clear()
            self.render()

    def confirm(self):
        if not self.cart:
            messages.show_warning(self, 'Корзина пуста. Добавьте товар из каталога.')
            return
        if not messages.ask_confirmation(self, 'Оформить заказ из {} позиций?'.format(len(self.cart))):
            return
        try:
            number = orders.create_order(self.customer_user_id, self.cart)
        except (ValueError, Exception) as exc:
            messages.show_error(self, 'Не удалось оформить заказ: {}. Обновите остатки.'.format(exc))
            return
        self.cart.clear()
        messages.show_info(self, 'Заказ №{} успешно оформлен.'.format(number))
        self.placed.emit()
        self.accept()


class OrderDialog(QDialog):
    """Просмотр заказа для менеджера и редактирование для администратора."""
    changed = pyqtSignal()

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.order = orders.get_order(order_id)
        if self.order is None:
            raise ValueError('Заказ не найден.')
        self.admin = users.is_admin(auth_controller.current_user())
        self.removed_ids = set()
        self.setWindowTitle('Чудо Обувь — Заказ №{}'.format(order_id))
        self.resize(770, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(label('Клиент: ' + self.order['full_name'], True))
        top = QHBoxLayout()
        top.addWidget(label('Дата заказа:'))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('dd.MM.yyyy')
        self.date_edit.setDate(QDate.fromString(str(self.order['order_date']), 'yyyy-MM-dd'))
        self.date_edit.setEnabled(self.admin)
        top.addWidget(self.date_edit)
        top.addStretch()
        layout.addLayout(top)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['Модель', 'Производство', 'Размер', 'Шт.', 'Цена', 'Сумма'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.total_label = label('')
        layout.addWidget(self.total_label)
        buttons = QHBoxLayout()
        if self.admin:
            remove = QPushButton('Удалить выбранную позицию')
            remove.setObjectName('secondaryButton')
            remove.clicked.connect(self.remove_selected)
            buttons.addWidget(remove)
        back = QPushButton('Назад')
        back.setObjectName('secondaryButton')
        back.clicked.connect(self.reject)
        buttons.addWidget(back)
        if self.admin:
            save = QPushButton('Сохранить изменения')
            save.clicked.connect(self.save)
            buttons.addWidget(save)
        layout.addLayout(buttons)
        self.render()

    def render(self):
        visible = [i for i in self.order['items'] if i['order_item_id'] not in self.removed_ids]
        self.table.setRowCount(0)
        total = Decimal('0')
        for item in visible:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, text in enumerate([
                item['product_name'], item['manufacturer_name'], str(item['size_value']),
                str(item['quantity']), money(item['price']), money(item['price'] * item['quantity'])
            ]):
                self.table.setItem(row, col, QTableWidgetItem(text))
            total += item['price'] * item['quantity']
        self.visible = visible
        self.total_label.setText('Итого: ' + money(total))

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            messages.show_warning(self, 'Выберите позицию в таблице.')
            return
        if len(self.visible) == 1:
            messages.show_warning(self, 'Нельзя удалить последнюю позицию. Удалите заказ целиком.')
            return
        if messages.ask_confirmation(self, 'Удалить выбранную позицию при сохранении заказа?'):
            self.removed_ids.add(self.visible[row]['order_item_id'])
            self.render()

    def save(self):
        if not self.admin:
            messages.show_error(self, 'Редактирование доступно только администратору.')
            return
        try:
            orders.update_order(self.order_id, self.date_edit.date().toString('yyyy-MM-dd'), self.removed_ids)
        except Exception as exc:
            messages.show_error(self, 'Не удалось сохранить заказ: {}'.format(exc))
            return
        messages.show_info(self, 'Изменения заказа сохранены.')
        self.changed.emit()
        self.accept()


class MainWindow(QMainWindow):
    """Каталог, поиск в реальном времени, управление заказами по ролям."""
    logged_out = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.cart = []
        self.customer_override = None
        self.setWindowTitle('Чудо Обувь — Каталог')
        self.setWindowIcon(QIcon(str(IMAGES / 'icon.ico')))
        self.resize(1130, 760)
        outer = QWidget()
        self.setCentralWidget(outer)
        main = QVBoxLayout(outer)
        header = QHBoxLayout()
        header.addWidget(image_label('logo.png', 95, 58))
        heading = label('Чудо Обувь', True)
        heading.setObjectName('windowTitle')
        header.addWidget(heading)
        header.addStretch()
        user = auth_controller.current_user()
        self.identity = label(user['full_name'] if user else 'Гость')
        header.addWidget(self.identity)
        self.btn_catalog = QPushButton('Каталог')
        self.btn_catalog.clicked.connect(self.show_catalog)
        header.addWidget(self.btn_catalog)
        self.btn_cart = QPushButton('Корзина')
        self.btn_cart.clicked.connect(self.show_cart)
        self.btn_cart.setVisible(bool(user))
        header.addWidget(self.btn_cart)
        self.btn_orders = QPushButton('Заказы')
        self.btn_orders.clicked.connect(self.show_orders)
        self.btn_orders.setVisible(users.can_manage_orders(user))
        header.addWidget(self.btn_orders)
        log_out = QPushButton('Выйти')
        log_out.setObjectName('secondaryButton')
        log_out.clicked.connect(self.exit_to_login)
        header.addWidget(log_out)
        main.addLayout(header)
        self.stack = QStackedWidget()
        main.addWidget(self.stack)
        self.catalog = QWidget()
        catalog_layout = QVBoxLayout(self.catalog)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Поиск по наименованию и описанию')
        self.search.textChanged.connect(self.reload_catalog)
        filters.addWidget(self.search, 3)
        self.categories = QComboBox()
        self.categories.addItem('Все категории', None)
        for c in products.list_categories():
            self.categories.addItem(c['category_name'], c['category_id'])
        self.categories.currentIndexChanged.connect(self.reload_catalog)
        filters.addWidget(self.categories, 1)
        self.sort = QComboBox()
        self.sort.addItem('Без сортировки', '')
        self.sort.addItem('Цена: по возрастанию', 'price_asc')
        self.sort.addItem('Цена: по убыванию', 'price_desc')
        self.sort.currentIndexChanged.connect(self.reload_catalog)
        filters.addWidget(self.sort, 1)
        self.filters = QWidget()
        self.filters.setLayout(filters)
        self.filters.setVisible(bool(user))
        catalog_layout.addWidget(self.filters)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.cards_host)
        catalog_layout.addWidget(self.scroll)
        self.stack.addWidget(self.catalog)
        self.orders_page = QWidget()
        orders_layout = QVBoxLayout(self.orders_page)
        title = label('Заказы клиентов', True)
        title.setObjectName('windowTitle')
        orders_layout.addWidget(title)
        self.orders_table = QTableWidget(0, 5)
        self.orders_table.setHorizontalHeaderLabels(['№ заказа', 'Дата', 'ФИО клиента', 'Итого', 'Действия'])
        self.orders_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        orders_layout.addWidget(self.orders_table)
        buttons = QHBoxLayout()
        create = QPushButton('Добавить новый заказ')
        create.clicked.connect(self.start_customer_order)
        buttons.addWidget(create)
        back = QPushButton('Назад в каталог')
        back.setObjectName('secondaryButton')
        back.clicked.connect(self.show_catalog)
        buttons.addWidget(back)
        orders_layout.addLayout(buttons)
        self.stack.addWidget(self.orders_page)
        self.reload_catalog()
        self.update_cart_button()

    def update_cart_button(self):
        self.btn_cart.setText('Корзина ({})'.format(sum(int(i['quantity']) for i in self.cart)))

    def clear_layout(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def reload_catalog(self, *_):
        self.clear_layout()
        try:
            rows = products.list_products(self.categories.currentData(), self.search.text(), self.sort.currentData())
        except Exception as exc:
            messages.show_error(self, 'Не удалось загрузить каталог: {}'.format(exc))
            return
        if not rows:
            self.cards_layout.addWidget(label('По вашему запросу товары не найдены.'))
        for p in rows:
            card = QFrame()
            card.setObjectName('lowStock' if p['is_low_stock'] else 'productCard')
            line = QHBoxLayout(card)
            line.addWidget(image_label(p['image_path'], 130, 100))
            info = QVBoxLayout()
            info.addWidget(label('{} | {}'.format(p['manufacturer_name'], p['product_name']), True))
            info.addWidget(label('Категория: {}'.format(p['category_name'])))
            info.addWidget(label('Количество: {} пар'.format(p['total_quantity'])))
            info.addWidget(label('Состав: {}'.format(p['composition'] or 'Нет данных')))
            line.addLayout(info, 1)
            price_box = QVBoxLayout()
            price_box.addWidget(label(money(p['final_price']), True))
            if p['discount_percent']:
                price_box.addWidget(label('Скидка 25%'))
            button = QPushButton('Подробнее')
            button.clicked.connect(lambda _, ident=p['product_id']: self.open_product(ident))
            price_box.addWidget(button)
            line.addLayout(price_box)
            self.cards_layout.addWidget(card)
        self.cards_layout.addStretch()

    def open_product(self, product_id):
        try:
            dialog = ProductDialog(product_id, self)
            dialog.added.connect(self.add_to_cart)
            dialog.exec_()
        except Exception as exc:
            messages.show_error(self, 'Не удалось открыть товар: {}'.format(exc))

    def add_to_cart(self, item):
        for existing in self.cart:
            if existing['stock_item_id'] == item['stock_item_id']:
                if existing['quantity'] + item['quantity'] > item['available']:
                    messages.show_warning(self, 'На складе недостаточно пар этого размера.')
                    return
                existing['quantity'] += item['quantity']
                self.update_cart_button()
                messages.show_info(self, 'Количество в корзине увеличено.')
                return
        self.cart.append(item)
        self.update_cart_button()
        messages.show_info(self, 'Товар добавлен в корзину.')

    def show_cart(self):
        user = auth_controller.current_user()
        if not user:
            messages.show_warning(self, 'Для заказа необходимо авторизоваться.')
            return
        customer_id = self.customer_override or user['user_id']
        dialog = CartDialog(self.cart, customer_id, self)
        dialog.placed.connect(self.order_placed)
        dialog.exec_()
        self.update_cart_button()

    def order_placed(self):
        self.customer_override = None
        self.reload_catalog()
        self.update_cart_button()
        if users.can_manage_orders(auth_controller.current_user()):
            self.reload_orders()

    def show_catalog(self):
        self.setWindowTitle('Чудо Обувь — Каталог')
        self.reload_catalog()
        self.stack.setCurrentWidget(self.catalog)

    def show_orders(self):
        if not users.can_manage_orders(auth_controller.current_user()):
            messages.show_error(self, 'Доступ к заказам запрещён.')
            return
        self.setWindowTitle('Чудо Обувь — Заказы')
        self.reload_orders()
        self.stack.setCurrentWidget(self.orders_page)

    def reload_orders(self):
        try:
            records = orders.list_orders()
        except Exception as exc:
            messages.show_error(self, 'Не удалось загрузить заказы: {}'.format(exc))
            return
        self.orders_table.setRowCount(0)
        for order in records:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            for col, value in enumerate([order['order_id'], order['order_date'], order['full_name'], money(order['total'])]):
                self.orders_table.setItem(row, col, QTableWidgetItem(str(value)))
            controls = QWidget()
            bar = QHBoxLayout(controls)
            bar.setContentsMargins(1, 1, 1, 1)
            op = QPushButton('Просмотр')
            op.clicked.connect(lambda _, ident=order['order_id']: self.open_order(ident))
            bar.addWidget(op)
            de = QPushButton('Удалить')
            de.setObjectName('secondaryButton')
            de.clicked.connect(lambda _, ident=order['order_id']: self.delete_order(ident))
            bar.addWidget(de)
            self.orders_table.setCellWidget(row, 4, controls)

    def open_order(self, order_id):
        try:
            dialog = OrderDialog(order_id, self)
            dialog.changed.connect(self.after_order_change)
            dialog.exec_()
        except Exception as exc:
            messages.show_error(self, 'Не удалось открыть заказ: {}'.format(exc))

    def delete_order(self, order_id):
        if not users.can_manage_orders(auth_controller.current_user()):
            messages.show_error(self, 'Операция запрещена.')
            return
        if not messages.ask_confirmation(self, 'Удалить заказ №{} и вернуть товары на склад?'.format(order_id)):
            return
        try:
            orders.delete_order(order_id)
        except Exception as exc:
            messages.show_error(self, 'Не удалось удалить заказ: {}'.format(exc))
            return
        messages.show_info(self, 'Заказ удалён.')
        self.after_order_change()

    def after_order_change(self):
        self.reload_orders()
        self.reload_catalog()

    def start_customer_order(self):
        if not users.can_manage_orders(auth_controller.current_user()):
            messages.show_error(self, 'Операция запрещена.')
            return
        try:
            customers = users.list_all()
        except Exception as exc:
            messages.show_error(self, 'Не удалось загрузить клиентов: {}'.format(exc))
            return
        choices = ['{} — {} ({})'.format(u['full_name'], u['login'], u['role_name']) for u in customers]
        chosen, ok = QInputDialog.getItem(self, 'Чудо Обувь — Новый заказ', 'Для какого клиента создать заказ?', choices, 0, False)
        if not ok:
            return
        if self.cart and not messages.ask_confirmation(self, 'Очистить текущую корзину перед созданием нового заказа?'):
            return
        self.cart.clear()
        self.customer_override = customers[choices.index(chosen)]['user_id']
        self.update_cart_button()
        self.show_catalog()
        messages.show_info(self, 'Выберите товар и размер, затем откройте корзину. Заказ оформится для выбранного клиента.')

    def exit_to_login(self):
        if self.cart and not messages.ask_confirmation(self, 'В корзине есть товары. Выйти без оформления?'):
            return
        auth_controller.logout()
        self.logged_out.emit()
        self.close()


class AppController:
    """При выходе открывает вход заново, не завершая приложение."""
    def __init__(self):
        self.login = None
        self.main = None
        self.show_login()

    def show_login(self):
        self.login = LoginWindow()
        self.login.entered.connect(self.show_main)
        self.login.show()

    def show_main(self):
        try:
            self.main = MainWindow()
        except Exception as exc:
            messages.show_error(self.login, 'Не удалось открыть приложение: {}'.format(exc))
            return
        self.main.logged_out.connect(self.show_login)
        self.main.show()
        self.login.close()

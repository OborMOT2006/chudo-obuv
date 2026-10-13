"""Точка входа в настольное приложение «Чудо Обувь»."""
import sys
from pathlib import Path
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from db.connection import check_connection
from utils import messages
from views.app_window import AppController

ROOT = Path(__file__).resolve().parent


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Чудо Обувь')
    app.setWindowIcon(QIcon(str(ROOT / 'resources' / 'images' / 'icon.ico')))
    app.setQuitOnLastWindowClosed(True)
    style_path = ROOT / 'resources' / 'styles' / 'style.qss'
    if style_path.is_file():
        app.setStyleSheet(style_path.read_text(encoding='utf-8'))
    try:
        check_connection()
    except Exception as exc:
        messages.show_error(None, 'Нет соединения с PostgreSQL. Проверьте DB_HOST, DB_NAME, DB_USER, DB_PASSWORD и запуск сервера.\n\n{}'.format(exc))
        return 1
    controller = AppController()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())

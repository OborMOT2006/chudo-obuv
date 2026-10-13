"""Обновляет db/data.sql из XLSX и импортирует данные в ПУСТУЮ схему PostgreSQL."""
from pathlib import Path
from scripts.build_data_sql import main as build_sql
from db.connection import transaction


def main():
    build_sql()
    text = (Path(__file__).resolve().parent / 'data.sql').read_text(encoding='utf-8')
    with transaction() as cursor:
        cursor.execute('SELECT COUNT(*) FROM products')
        if cursor.fetchone()[0]:
            raise RuntimeError('База не пуста: повторный импорт запрещён. Данные не изменены.')
        # Убираем внешние BEGIN/COMMIT — транзакцией управляет contextmanager.
        lines = [s for s in text.splitlines() if s.strip() not in ('BEGIN;', 'COMMIT;')]
        cursor.execute('\n'.join(lines))
    print('Импорт выполнен успешно.')


if __name__ == '__main__':
    main()

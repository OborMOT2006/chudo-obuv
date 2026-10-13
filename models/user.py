"""Пользователи и роли. Пароли не нужны по условиям учебного кейса."""
from db.connection import fetch_one, fetch_all


def find_by_login(login):
    return fetch_one('''
        SELECT u.user_id, u.login, u.last_name, u.first_name, u.middle_name, r.role_name,
               TRIM(u.last_name || ' ' || u.first_name || ' ' || COALESCE(u.middle_name, '')) AS full_name
        FROM users u JOIN roles r ON r.role_id = u.role_id
        WHERE u.login = %s
    ''', (login.strip(),))


def list_all():
    return fetch_all('''
        SELECT u.user_id, u.login,
               TRIM(u.last_name || ' ' || u.first_name || ' ' || COALESCE(u.middle_name, '')) AS full_name,
               r.role_name
        FROM users u JOIN roles r ON r.role_id = u.role_id
        ORDER BY u.last_name, u.first_name
    ''')


def can_manage_orders(user):
    return bool(user and user['role_name'] in ('Менеджер', 'Администратор'))


def is_admin(user):
    return bool(user and user['role_name'] == 'Администратор')

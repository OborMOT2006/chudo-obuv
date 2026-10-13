"""Текущий пользователь: None означает режим гостя."""
from models import user as users

_current_user = None


def login(login_name):
    global _current_user
    result = users.find_by_login(login_name.strip())
    if not result:
        return False, 'Пользователь с таким логином не найден.'
    _current_user = result
    return True, ''


def guest():
    global _current_user
    _current_user = None


def current_user():
    return _current_user


def logout():
    guest()

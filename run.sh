#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ -f config_local.sh ]; then
    source ./config_local.sh
fi
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    echo 'Окружение .venv отсутствует. Сначала выполните: python3 -m venv .venv'
    exit 1
fi
if [ -z "${DB_PASSWORD:-}" ]; then
    read -r -s -p 'Пароль PostgreSQL: ' DB_PASSWORD
    echo
    export DB_PASSWORD
fi
python main.py

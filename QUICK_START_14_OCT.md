# Быстрый запуск на MOS Linux / ROSA

**14 октября (есть интернет):** установить программы, Python-библиотеки и JDBC-драйвер DBeaver. **15 октября (без интернета):** только запускать то, что уже проверено.

## 1. Установка

```bash
cd ~
sudo dnf install -y postgresql-server postgresql-contrib python3 python3-pip git vscode dbeaver libreoffice
```

## 2. PostgreSQL

```bash
sudo systemctl enable --now postgresql12
cd /tmp
sudo -u postgres psql -c "SELECT version();"
sudo -u postgres psql
```

**Внутри `psql`:**

```text
\password postgres
\q
```

Если ошибка прав на `/var/log/postgres/postgresql`, применить исправление из README. Если служба называется по-другому, уточнить имя через `systemctl list-unit-files | grep -i postgres`.

## 3. Проект и виртуальное окружение

Предполагается, что папка `Chudo_Obuv_GitHub` уже находится в `/home/live/` (заранее распаковали ZIP либо клонировали GitHub):

```bash
cd ~/Chudo_Obuv_GitHub
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 4. База (только для новой пустой базы!)

```bash
sudo -u postgres createdb shoe_store
sudo -u postgres psql -v ON_ERROR_STOP=1 -d shoe_store < db/schema.sql
sudo -u postgres psql -v ON_ERROR_STOP=1 -d shoe_store < db/data.sql
```

**ОСТОРОЖНО:** schema.sql уничтожает старую базовую структуру. При наличии данных НЕ запускать повторно.

## 5. Подключение приложения

```bash
cp config_local.sh.example config_local.sh
code .
```

В файле `config_local.sh` заменить пример пароля на собственный пароль PostgreSQL. Затем в терминале:

```bash
cd ~/Chudo_Obuv_GitHub
./run.sh
```

## 6. DBeaver — офлайн

Открыть `dbeaver`, скачать JDBC-драйвер PostgreSQL **ещё 14 октября**, сделать Test Connection (host `127.0.0.1`, порт `5432`, БД `shoe_store`, user `postgres`, свой пароль). 15 октября скачивать будет негде.

## 7. Проверка

- Приложение открывается, логины `isivanov`, `papetrov`, `asidorova` работают.
- Каталог отображает 34 модели; можно оформить заказ и увидеть изменение остатков.
- DBeaver подключается к базе `shoe_store`.
- `docs/ERD_module_1.pdf` открывается.
- Для 5-го модуля доступен `analytics/run_analytics.py`; исходные CSV Приложения 4 организаторы должны предоставить отдельно.

**Выход из `.venv`:** `deactivate`. **Вход после нового открытия терминала:** `cd ~/Chudo_Obuv_GitHub` и `source .venv/bin/activate`.

**Разрешение на подготовленные файлы:** уточнить у преподавателя/организаторов до экзамена. При запрете скачивания готовых работ изучать как тренировочный проект.

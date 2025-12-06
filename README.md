# Transactional System Core

Система обработки транзакций с защитой от race condition и асинхронными уведомлениями.

## Технологии

- Python 3.11+
- Django 4.2
- Django REST Framework
- Celery 5.3
- Redis (порт 6380)
- PostgreSQL

## Установка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных

Создайте базу данных PostgreSQL и настройте переменные окружения:

```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками БД
```

### 3. Применение миграций

```bash
python manage.py migrate
```

### 4. Создание тестовых кошельков

```bash
python manage.py create_test_wallets
```

Это создаст два тестовых кошелька:
- Wallet 1: user_id=1, balance=10000
- Wallet 2: user_id=2, balance=1000
- Admin Wallet: user_id=0, balance=0 (для комиссий)

### 5. Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

## Запуск

### Запуск Django сервера

```bash
python manage.py runserver
```

### Запуск Celery worker (локально)

```bash
celery -A transactional_system worker --loglevel=info
```

### Запуск через Docker (Celery + Redis)

```bash
docker-compose up -d
```

Это запустит:
- Redis на порту **6380** (нестандартный порт)
- Celery worker в контейнере

## API

### POST /api/transfer

Перевод средств между кошельками.

**Запрос:**
```json
{
    "from_wallet_id": 1,
    "to_wallet_id": 2,
    "amount": "1500.00"
}
```

**Ответ (успех):**
```json
{
    "message": "Перевод выполнен успешно",
    "transaction": {
        "id": 1,
        "from_wallet": {...},
        "to_wallet": {...},
        "amount": "1500.00",
        "transaction_type": "transfer",
        "status": "completed",
        "commission_amount": "150.00",
        "created_at": "2024-01-01T12:00:00Z"
    },
    "commission": "150.00"
}
```

## Особенности реализации

### 1. Защита от Race Condition

Используется `select_for_update()` для блокировки строк в БД и атомарные операции через `F()` expressions. Это предотвращает двойное списание при параллельных запросах.

### 2. Комиссия системы

- Если сумма перевода > 1000, система берет комиссию 10%
- Комиссия зачисляется на специальный админский кошелек (user_id=0)
- Все операции выполняются атомарно (либо все, либо ничего)

### 3. Асинхронные уведомления

После успешной транзакции отправляется уведомление через Celery:
- Имитация долгого запроса (5 секунд)
- Автоматический retry при ошибке (3 попытки, интервал 3 секунды)

## Тестирование

### Быстрый тест через скрипт

```bash
# Убедитесь, что сервер запущен, затем:
python test_transfer.py
```

### Тест на race condition

Можно использовать Apache Bench или аналогичный инструмент:

```bash
# Создайте файл transfer.json:
echo '{"from_wallet_id": 1, "to_wallet_id": 2, "amount": "10.00"}' > transfer.json

# Запустите тест:
ab -n 100 -c 10 -p transfer.json -T application/json http://localhost:8000/api/transfer
```

Или используйте встроенный тест в `test_transfer.py` (раскомментируйте строку с `test_race_condition`).

### Тест уведомлений

Для тестирования retry механизма, раскомментируйте строку в `wallets/tasks.py`:
```python
if random.random() < 0.5:
    raise Exception("Simulated notification error")
```

Затем выполните перевод и наблюдайте логи Celery worker - вы увидите попытки retry при ошибках.

## Структура проекта

```
transactional_system/
├── transactional_system/    # Основные настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── wallets/                 # Приложение для кошельков и транзакций
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── tasks.py
│   └── urls.py
├── docker-compose.yml
├── Dockerfile.celery
└── requirements.txt
```


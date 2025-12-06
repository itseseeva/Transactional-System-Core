# Примеры использования API

## Базовый перевод

```bash
curl -X POST http://localhost:8000/api/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_wallet_id": 1,
    "to_wallet_id": 2,
    "amount": "500.00"
  }'
```

**Ответ:**
```json
{
  "message": "Перевод выполнен успешно",
  "transaction": {
    "id": 1,
    "from_wallet": {
      "id": 1,
      "user_id": 1,
      "balance": "9500.00"
    },
    "to_wallet": {
      "id": 2,
      "user_id": 2,
      "balance": "1500.00"
    },
    "amount": "500.00",
    "transaction_type": "transfer",
    "status": "completed",
    "commission_amount": "0.00"
  },
  "commission": "0.00"
}
```

## Перевод с комиссией (> 1000)

```bash
curl -X POST http://localhost:8000/api/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_wallet_id": 1,
    "to_wallet_id": 2,
    "amount": "1500.00"
  }'
```

**Ответ:**
```json
{
  "message": "Перевод выполнен успешно",
  "transaction": {
    "id": 2,
    "from_wallet": {
      "id": 1,
      "user_id": 1,
      "balance": "7850.00"
    },
    "to_wallet": {
      "id": 2,
      "user_id": 2,
      "balance": "3000.00"
    },
    "amount": "1500.00",
    "transaction_type": "transfer",
    "status": "completed",
    "commission_amount": "150.00"
  },
  "commission": "150.00"
}
```

**Что произошло:**
- Списалось: 1500.00 (сумма) + 150.00 (10% комиссия) = 1650.00
- Зачислено получателю: 1500.00
- Зачислено на админский кошелек: 150.00

## Ошибки

### Недостаточно средств
```json
{
  "error": "Недостаточно средств на кошельке отправителя"
}
```

### Кошелек не найден
```json
{
  "error": "Один из кошельков не найден"
}
```

### Перевод самому себе
```json
{
  "error": "Нельзя переводить средства на тот же кошелек"
}
```

## Проверка уведомлений

После успешного перевода:
1. Задача отправляется в Celery
2. В логах Celery worker вы увидите:
   ```
   [Celery Task] Отправка уведомления для транзакции 1...
   [Celery Task] Уведомление успешно отправлено для транзакции 1
   ```

3. При ошибке (если раскомментирован тест в tasks.py):
   ```
   [Celery Task] Ошибка при отправке уведомления (попытка 1/3): ...
   [Celery Task] Ошибка при отправке уведомления (попытка 2/3): ...
   ```


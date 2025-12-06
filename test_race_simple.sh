#!/bin/bash
# Простой скрипт для тестирования race condition через curl

echo "Тест Race Condition: 10 одновременных запросов"
echo "=============================================="
echo ""

# Параметры
FROM_WALLET=1
TO_WALLET=2
AMOUNT=100.00
NUM_REQUESTS=10

# Функция для выполнения одного запроса
make_request() {
    local request_num=$1
    response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transfer \
        -H "Content-Type: application/json" \
        -d "{\"from_wallet_id\": $FROM_WALLET, \"to_wallet_id\": $TO_WALLET, \"amount\": \"$AMOUNT\"}")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq 201 ]; then
        echo "✓ Запрос $request_num: УСПЕХ"
    else
        error=$(echo "$body" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
        echo "✗ Запрос $request_num: ОШИБКА ($http_code) - $error"
    fi
}

# Запускаем запросы в фоне
echo "Запуск $NUM_REQUESTS одновременных запросов..."
echo ""

for i in $(seq 1 $NUM_REQUESTS); do
    make_request $i &
done

# Ждем завершения всех фоновых процессов
wait

echo ""
echo "Тест завершен!"


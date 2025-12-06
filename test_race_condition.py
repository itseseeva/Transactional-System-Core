"""
Скрипт для тестирования защиты от Race Condition.
Делает 10 одновременных запросов на списание и проверяет, что баланс не уходит в минус.

Использование:
    python test_race_condition.py [from_wallet_id] [to_wallet_id] [amount] [num_requests]
    
Пример:
    python test_race_condition.py 1 2 100.00 10
"""
import requests
import json
import time
import sys
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api"

def get_wallet_balance(wallet_id):
    """Получить баланс кошелька через API"""
    url = f"{BASE_URL}/wallet/{wallet_id}/balance"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return Decimal(str(response.json()['balance']))
        return None
    except Exception:
        return None

def transfer(from_wallet_id, to_wallet_id, amount):
    """Выполнение перевода"""
    url = f"{BASE_URL}/transfer"
    data = {
        "from_wallet_id": from_wallet_id,
        "to_wallet_id": to_wallet_id,
        "amount": str(amount)
    }
    try:
        response = requests.post(url, json=data, timeout=30)  # Увеличен таймаут для параллельных запросов
        return {
            'status_code': response.status_code,
            'response': response.json() if response.status_code < 500 else {'error': 'Server error'},
            'success': response.status_code == 201
        }
    except Exception as e:
        return {
            'status_code': 0,
            'response': {'error': str(e)},
            'success': False
        }

def test_race_condition(from_wallet_id, to_wallet_id, amount_per_request, num_requests=10):
    """
    Тест на race condition: делает N одновременных запросов на списание.
    Проверяет, что баланс не уходит в минус.
    """
    print("=" * 70)
    print(f"ТЕСТ ЗАЩИТЫ ОТ RACE CONDITION")
    print("=" * 70)
    print(f"Кошелек отправителя: {from_wallet_id}")
    print(f"Кошелек получателя: {to_wallet_id}")
    print(f"Сумма одного запроса: {amount_per_request}")
    print(f"Количество одновременных запросов: {num_requests}")
    print(f"Общая сумма всех запросов: {amount_per_request * num_requests}")
    print()
    
    # Получаем начальный баланс
    print("Получение начального баланса...")
    initial_balance = get_wallet_balance(from_wallet_id)
    if initial_balance is not None:
        print(f"Начальный баланс кошелька {from_wallet_id}: {initial_balance}")
        if initial_balance < amount_per_request * num_requests:
            print(f"⚠️  ВНИМАНИЕ: Баланс ({initial_balance}) меньше суммы всех запросов ({amount_per_request * num_requests})")
            print("   Некоторые запросы будут отклонены - это нормально для теста!")
    else:
        print("⚠️  Не удалось получить баланс. Продолжаем тест...")
    print()
    
    print("Запуск одновременных запросов...")
    print("-" * 70)
    
    start_time = time.time()
    successful = 0
    failed = 0
    failed_reasons = {}
    results = []
    
    def make_request(request_num):
        """Выполнить один запрос"""
        result = transfer(from_wallet_id, to_wallet_id, amount_per_request)
        result['request_num'] = request_num
        return result
    
    # Запускаем все запросы одновременно
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = {
            executor.submit(make_request, i+1): i+1 
            for i in range(num_requests)
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                
                if result['success']:
                    successful += 1
                    print(f"✓ Запрос {result['request_num']}: УСПЕХ")
                else:
                    failed += 1
                    error_msg = result['response'].get('error', 'Unknown error')
                    print(f"✗ Запрос {result['request_num']}: ОШИБКА - {error_msg}")
                    
                    # Подсчитываем причины ошибок
                    if error_msg not in failed_reasons:
                        failed_reasons[error_msg] = 0
                    failed_reasons[error_msg] += 1
                    
            except Exception as e:
                failed += 1
                print(f"✗ Исключение: {e}")
    
    elapsed = time.time() - start_time
    
    print("-" * 70)
    print("РЕЗУЛЬТАТЫ ТЕСТА:")
    print("-" * 70)
    print(f"Успешных транзакций: {successful}")
    print(f"Отклоненных транзакций: {failed}")
    print(f"Время выполнения: {elapsed:.2f} секунд")
    print()
    
    if failed_reasons:
        print("Причины отклонений:")
        for reason, count in failed_reasons.items():
            print(f"  - {reason}: {count}")
        print()
    
    # Проверка: баланс не должен уйти в минус
    total_deducted = successful * amount_per_request
    print(f"Общая сумма успешно списанных средств: {total_deducted}")
    
    # Получаем финальный баланс
    final_balance = get_wallet_balance(from_wallet_id)
    if initial_balance is not None and final_balance is not None:
        print(f"Начальный баланс: {initial_balance}")
        print(f"Финальный баланс: {final_balance}")
        print(f"Списано: {initial_balance - final_balance}")
        print(f"Ожидалось списать: {total_deducted}")
        
        # Проверка: баланс не должен быть отрицательным
        if final_balance < 0:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Баланс ушел в минус!")
        else:
            print("✅ Баланс не ушел в минус - защита работает!")
    print()
    print("=" * 70)
    
    return {
        'successful': successful,
        'failed': failed,
        'total_deducted': total_deducted,
        'elapsed': elapsed
    }

if __name__ == "__main__":
    import sys
    
    print()
    print("ТЕСТИРОВАНИЕ ЗАЩИТЫ ОТ RACE CONDITION")
    print()
    print("Этот скрипт делает 10 одновременных запросов на списание средств.")
    print("Система должна отклонить запросы, которые приведут к отрицательному балансу.")
    print()
    
    # Параметры теста
    FROM_WALLET_ID = 1  # ID кошелька отправителя
    TO_WALLET_ID = 2    # ID кошелька получателя
    AMOUNT_PER_REQUEST = 100.00  # Сумма одного запроса
    NUM_REQUESTS = 10   # Количество одновременных запросов
    
    # Можно передать параметры через аргументы командной строки
    if len(sys.argv) > 1:
        FROM_WALLET_ID = int(sys.argv[1])
    if len(sys.argv) > 2:
        TO_WALLET_ID = int(sys.argv[2])
    if len(sys.argv) > 3:
        AMOUNT_PER_REQUEST = float(sys.argv[3])
    if len(sys.argv) > 4:
        NUM_REQUESTS = int(sys.argv[4])
    
    try:
        # Проверяем доступность сервера
        response = requests.get(f"{BASE_URL.replace('/api', '')}/admin/", timeout=2)
        print("✓ Сервер доступен")
    except requests.exceptions.ConnectionError:
        print("✗ ОШИБКА: Не удалось подключиться к серверу.")
        print("  Убедитесь, что Django сервер запущен:")
        print("  python manage.py runserver")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Предупреждение: {e}")
    
    print()
    
    # Запускаем тест
    test_race_condition(
        from_wallet_id=FROM_WALLET_ID,
        to_wallet_id=TO_WALLET_ID,
        amount_per_request=AMOUNT_PER_REQUEST,
        num_requests=NUM_REQUESTS
    )


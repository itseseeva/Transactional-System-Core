from celery import shared_task
from celery.exceptions import Retry
import time
import random
from django.core.exceptions import ObjectDoesNotExist
from .models import Wallet, Transaction


@shared_task(bind=True, max_retries=3, default_retry_delay=3)
def send_transaction_notification(self, to_wallet_id, amount, transaction_id):
    """
    Задача для отправки уведомления получателю транзакции.
    
    Имитирует долгий запрос (time.sleep(5)).
    При ошибке автоматически перезапускается через 3 секунды, но не более 3 раз.
    """
    try:
        # Получаем информацию о транзакции и кошельке
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            wallet = Wallet.objects.get(id=to_wallet_id)
        except ObjectDoesNotExist:
            # Если транзакция или кошелек не найдены, не ретраим
            return {
                'status': 'error',
                'message': 'Transaction or wallet not found',
                'transaction_id': transaction_id
            }

        # Имитация долгого запроса (например, отправка в Telegram)
        print(f"[Celery Task] Отправка уведомления для транзакции {transaction_id}...")
        time.sleep(5)

        # Симуляция случайной ошибки (для тестирования retry механизма)
        # В реальности здесь был бы реальный API запрос
        # Раскомментируйте следующую строку для тестирования retry:
        # if random.random() < 0.5:  # 50% вероятность ошибки
        #     raise Exception("Simulated notification error")

        print(f"[Celery Task] Уведомление успешно отправлено для транзакции {transaction_id}")
        print(f"[Celery Task] Получатель: wallet_id={wallet.id}, user_id={wallet.user_id}")
        print(f"[Celery Task] Сумма: {amount}")

        return {
            'status': 'success',
            'message': 'Notification sent successfully',
            'transaction_id': transaction_id,
            'to_wallet_id': to_wallet_id,
            'amount': amount
        }

    except Exception as exc:
        # Логируем попытку
        print(f"[Celery Task] Ошибка при отправке уведомления (попытка {self.request.retries + 1}/3): {str(exc)}")
        
        # Автоматический retry через 3 секунды, максимум 3 попытки
        raise self.retry(exc=exc, countdown=3)


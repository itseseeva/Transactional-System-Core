from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import F
from decimal import Decimal
from .models import Wallet, Transaction
from .serializers import TransferSerializer, TransactionSerializer
from .tasks import send_transaction_notification


@api_view(['POST'])
def transfer(request):
    serializer = TransferSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    from_wallet_id = serializer.validated_data['from_wallet_id']
    to_wallet_id = serializer.validated_data['to_wallet_id']
    amount = serializer.validated_data['amount']

    if from_wallet_id == to_wallet_id:
        return Response(
            {'error': 'Нельзя переводить средства на тот же кошелек'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with db_transaction.atomic():
            from_wallet = Wallet.objects.select_for_update().get(id=from_wallet_id)
            to_wallet = Wallet.objects.select_for_update().get(id=to_wallet_id)

            if from_wallet.balance < amount:
                return Response(
                    {'error': 'Недостаточно средств на кошельке отправителя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            commission_rate = Decimal('0.10')
            commission_threshold = Decimal('1000.00')
            commission_amount = Decimal('0.00')
            
            if amount > commission_threshold:
                commission_amount = amount * commission_rate
                total_deduction = amount + commission_amount
                
                if from_wallet.balance < total_deduction:
                    return Response(
                        {'error': 'Недостаточно средств с учетом комиссии'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                total_deduction = amount

            if commission_amount > 0:
                try:
                    admin_wallet = Wallet.objects.select_for_update().get(user_id=0)
                except Wallet.DoesNotExist:
                    admin_wallet = Wallet.objects.create(
                        user_id=0,
                        balance=Decimal('0.00')
                    )

            Wallet.objects.filter(id=from_wallet.id).update(
                balance=F('balance') - total_deduction
            )
            
            Wallet.objects.filter(id=to_wallet.id).update(
                balance=F('balance') + amount
            )
            
            if commission_amount > 0:
                Wallet.objects.filter(id=admin_wallet.id).update(
                    balance=F('balance') + commission_amount
                )

            from_wallet.refresh_from_db()
            to_wallet.refresh_from_db()
            if commission_amount > 0:
                admin_wallet.refresh_from_db()

            main_transaction = Transaction.objects.create(
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                amount=amount,
                transaction_type='transfer',
                status='completed',
                commission_amount=commission_amount
            )

            if commission_amount > 0:
                Transaction.objects.create(
                    from_wallet=from_wallet,
                    to_wallet=admin_wallet,
                    amount=commission_amount,
                    transaction_type='commission',
                    status='completed',
                    commission_amount=Decimal('0.00')
                )

            # Сохраняем данные для уведомления
            transaction_id = main_transaction.id
            to_wallet_id_for_notification = to_wallet.id

        # Отправляем уведомление ПОСЛЕ завершения транзакции
        # Это важно, чтобы транзакция успела закоммититься и разблокировать строки
        try:
            send_transaction_notification.delay(
                to_wallet_id=to_wallet_id_for_notification,
                amount=str(amount),
                transaction_id=transaction_id
            )
        except Exception:
            # Если Celery не запущен, просто пропускаем уведомление
            # Это не критично для работы транзакций
            pass

        transaction_serializer = TransactionSerializer(main_transaction)
        return Response({
            'message': 'Перевод выполнен успешно',
            'transaction': transaction_serializer.data,
            'commission': str(commission_amount) if commission_amount > 0 else '0.00'
        }, status=status.HTTP_201_CREATED)

    except Wallet.DoesNotExist:
        return Response(
            {'error': 'Один из кошельков не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка при выполнении перевода: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def wallet_balance(request, wallet_id):
    """Получить баланс кошелька"""
    try:
        wallet = Wallet.objects.get(id=wallet_id)
        from .serializers import WalletSerializer  # Импортируем здесь, чтобы избежать ошибки "undefined name 'WalletSerializer'"
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Wallet.DoesNotExist:
        return Response(
            {'error': 'Кошелек не найден'},
            status=status.HTTP_404_NOT_FOUND
        )


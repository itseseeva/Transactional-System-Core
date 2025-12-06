from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Wallet(models.Model):
    """Кошелек пользователя"""
    user_id = models.IntegerField(unique=True, db_index=True, help_text="ID пользователя")
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Баланс кошелька"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        ordering = ['-created_at']

    def __str__(self):
        return f"Wallet(user_id={self.user_id}, balance={self.balance})"


class Transaction(models.Model):
    """Транзакция между кошельками"""
    TRANSACTION_TYPES = [
        ('transfer', 'Перевод'),
        ('commission', 'Комиссия'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('completed', 'Завершена'),
        ('failed', 'Ошибка'),
    ]

    from_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='outgoing_transactions',
        null=True,
        blank=True,
        help_text="Кошелек отправителя (null для комиссии)"
    )
    to_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='incoming_transactions',
        help_text="Кошелек получателя"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Сумма транзакции"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        default='transfer',
        help_text="Тип транзакции"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Статус транзакции"
    )
    commission_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Сумма комиссии"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_wallet', 'created_at']),
            models.Index(fields=['to_wallet', 'created_at']),
        ]

    def __str__(self):
        return f"Transaction({self.transaction_type}, {self.amount}, {self.status})"


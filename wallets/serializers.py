from rest_framework import serializers
from decimal import Decimal
from .models import Wallet, Transaction


class TransferSerializer(serializers.Serializer):
    """Сериализатор для перевода средств"""
    from_wallet_id = serializers.IntegerField(help_text="ID кошелька отправителя")
    to_wallet_id = serializers.IntegerField(help_text="ID кошелька получателя")
    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Сумма перевода"
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше нуля")
        return value


class WalletSerializer(serializers.ModelSerializer):
    """Сериализатор для кошелька"""
    class Meta:
        model = Wallet
        fields = ['id', 'user_id', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Сериализатор для транзакции"""
    from_wallet = WalletSerializer(read_only=True)
    to_wallet = WalletSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'from_wallet', 'to_wallet', 'amount',
            'transaction_type', 'status', 'commission_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


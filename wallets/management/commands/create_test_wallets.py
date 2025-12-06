from django.core.management.base import BaseCommand
from decimal import Decimal
from wallets.models import Wallet
import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class Command(BaseCommand):
    help = 'Creates test wallets for functionality testing'

    def handle(self, *args, **options):
        # Create test wallets
        wallet1, created1 = Wallet.objects.get_or_create(
            user_id=1,
            defaults={'balance': Decimal('10000.00')}
        )
        if created1:
            self.stdout.write(self.style.SUCCESS(f'Created wallet 1 (user_id=1, balance=10000)'))
        else:
            self.stdout.write(f'Wallet 1 already exists (user_id=1, balance={wallet1.balance})')

        wallet2, created2 = Wallet.objects.get_or_create(
            user_id=2,
            defaults={'balance': Decimal('1000.00')}
        )
        if created2:
            self.stdout.write(self.style.SUCCESS(f'Created wallet 2 (user_id=2, balance=1000)'))
        else:
            self.stdout.write(f'Wallet 2 already exists (user_id=2, balance={wallet2.balance})')

        # Admin wallet for commissions
        admin_wallet, created_admin = Wallet.objects.get_or_create(
            user_id=0,
            defaults={'balance': Decimal('0.00')}
        )
        if created_admin:
            self.stdout.write(self.style.SUCCESS(f'Created admin wallet (user_id=0, balance=0)'))
        else:
            self.stdout.write(f'Admin wallet already exists (user_id=0, balance={admin_wallet.balance})')

        self.stdout.write(self.style.SUCCESS('\nTest wallets ready!'))
        self.stdout.write(f'Wallet ID 1: {wallet1.id} (user_id={wallet1.user_id})')
        self.stdout.write(f'Wallet ID 2: {wallet2.id} (user_id={wallet2.user_id})')
        self.stdout.write(f'Admin Wallet ID: {admin_wallet.id} (user_id={admin_wallet.user_id})')


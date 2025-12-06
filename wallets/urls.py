from django.urls import path
from . import views

urlpatterns = [
    path('transfer', views.transfer, name='transfer'),
    path('wallet/<int:wallet_id>/balance', views.wallet_balance, name='wallet_balance'),
]


from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Главная страница
    path('', views.index2, name='index2'),

    # Бронирование
    path('booking_create/', views.booking_create, name='booking_create'),

    # Детали заказа
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # Политика конфеденциальности
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]


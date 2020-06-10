from django.urls import path
from .views import CartAddView

app_name = 'cart'

urlpatterns = [
    path('add', CartAddView.as_view(), name='add')  # 购物车记录添加
]

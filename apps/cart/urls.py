from django.urls import path
from .views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = 'cart'

urlpatterns = [
    path('add', CartAddView.as_view(), name='add'),  # 购物车记录添加
    path('', CartInfoView.as_view(), name='show'),  # 购物车页面显示
    path('update', CartUpdateView.as_view(), name='update'),  # 购物车页面显示
    path('delete', CartDeleteView.as_view(), name='delete'),  # 购物车记录删除
]

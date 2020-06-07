from django.urls import path, re_path
from django.contrib.auth.decorators import login_required
from .views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView

app_name = 'user'

urlpatterns = [
    # path('register/', views.register, name='register'),  # 注册
    # path('register_handle/', views.register_handle, name='register_handle'),  # 注册处理
    path('register/', RegisterView.as_view(), name='register'),  # 注册处理
    re_path('active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 用户激活
    path('login/', LoginView.as_view(), name='login'),  # 登录
    path('logout/', LogoutView.as_view(), name='logout'),  # 登录

    path('', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    path('order/', UserOrderView.as_view(), name='order'),  # 订单页
    path('address/', AddressView.as_view(), name='address'),  # 地址页

]

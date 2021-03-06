from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .models import User, Address
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.mail import send_mail
from django_redis import get_redis_connection
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin
from ..goods.models import GoodsSKU
from ..order.models import OrderInfo, OrderGoods
import re


class RegisterView(View):
    # 注册
    def get(self, request):
        # 显示注册页面
        return render(request, 'register.html')

    def post(self, request):
        # 进行注册处理
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            # 是否同意协议
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 进行业务处理:进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 发送激活邮件,包含激活连接:/user/active/
        # 激活链接中需要包含用户的身份信息,并且要把身份信息进行加密
        # 加密用户的身份信息,生成激活的token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf8')
        # 发邮件 -> redis来完成
        # Ubuntu终端命令:进入到项目所在位置, celery -A celery_tasks.tasks worker -l info
        send_register_active_email.delay(email, username, token)
        # 返回应答,跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    # 用户激活
    def get(self, request, token):
        # 进行解密,获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            token = token.split('/')[-1]
            info = serializer.loads(token)
            # 获取待激活用户的ID
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# /user/login
class LoginView(View):
    def get(self, request):
        # 显示登录页面
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        # 登录校验

        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 业务处理:
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户登录状态
                login(request, user)

                # 获取登录后所要跳转到的地址
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))

                # 跳转到next_url
                response = redirect(next_url)

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class LogoutView(View):
    def get(self, requesst):
        logout(requesst)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    # 用户信息
    def get(self, request):
        # request.user.is_authenticated()
        # 获取用户个人信息
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户最近浏览
        # from redis import StrictRedis
        # sr = StrictRedis(host='192.168.1.105', port='6379', db=9)
        con = get_redis_connection('default')

        history_key = 'history_{}'.format(user.id)

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        goods_li = []
        for iD in sku_ids:
            goods = GoodsSKU.objects.get(id=iD)
            goods_li.append(goods)

        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li,
        }

        # 除了你给模板文件传递模板变量之外,django会把request.user也传给模板文件
        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
    # 用户订单
    def get(self, request, page):
        # 获取用户订单
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性,保存订单状态的信息
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性,保存订单商品的信息
            order.order_skus = order_skus

        # 分页 1页4条
        paginator = Paginator(orders, 4)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo:进行页码的控制,页面上最多显示5个页码
        # 1.总页数小于5页,页面上显示所有页码
        # 2.如果当前页是前三页,显示1-5页
        # 3.如果当前页是后三页,显示后5页
        # 4.其他情况,显示当前页的前两页,当前页,当前页的后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order',
        }
        # 使用模板
        return render(request, 'user_center_order.html', context=context)


class AddressView(LoginRequiredMixin, View):
    # 用户地址
    def get(self, request):
        # 获取用户的默认收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 地址添加

        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([addr, receiver, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号码不正确'})

        # 业务处理:地址添加
        # 获取登录用户对应的User对象
        user = request.user

        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        Address.objects.create(user=user, addr=addr, receiver=receiver,
                               zip_code=zip_code, phone=phone, is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address'))

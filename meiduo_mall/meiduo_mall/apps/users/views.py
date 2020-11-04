from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
import json
import re
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from django.middleware.csrf import get_token

from areas.models import Area
from users.models import User
from django.http import JsonResponse, response
from meiduo_mall.utils.mixins import LoginRequiredMixin
from users.models import Address

# GET /usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
class UsernameCountView(View):
    def get(self, request, username):
        """判断注册用户名是否重复"""
        #根据 username 查询数据库获取对应用户的数量
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败!'})
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'count': count})

# GET /mobiles/(?P<mobile>1[3-9]\d{9})/count/
class MobileCountView(View):
    def get(self, request, mobile):
        """判断注册手机号是否重复"""
        #查询数据库判断mobile是否存在
        try:
            count = User.objects.filter(moblie=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败!'})
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'count': count})

# POST /register/
class RegisterView(View):

    def post(self, request):
        """用户信息存储"""
        req_data = json.loads(request.body.decode())
        username = req_data.get('username')
        password = req_data.get('password')
        password2 = req_data.get('password2')
        mobile = req_data.get('mobile')
        allow = req_data.get('allow')
        sms_code = req_data.get('sms_code')

        # 1,判断输入完整性
        if not all([username, password, password2, mobile, allow, sms_code]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})
        # 2,判断用户名输入格式
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400,
                                 'message': '用户名格式错误'})
        # 3,判断密码输入格式
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'message': '密码格式错误'})
        # 4,判断两次密码输入是否相同
        if password != password2:
            return JsonResponse({'code': 400,
                                 'message': '两次密码不一致'})
        # 5,判断手机号输入格式
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'message': '手机号格式错误'})
        # 6,判断是否同意协议
        if not allow:
            return JsonResponse({'code': 400,
                                 'message': '请同意协议!'})
        # 7,短信验证码校验
        redis_conn = get_redis_connection('verify_code')
        sms_code_redis = redis_conn.get('sms_%s' % mobile)
        # 7.1 判断验证码正确
        if sms_code != sms_code_redis:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码错误'})
        # 7.2 判断验证码是否过期
        if not sms_code_redis:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码过期'})

        # 保存新增用户数据到数据库
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '数据库保存错误'})

        # 保存登录状态信息
        from django.contrib.auth import login
        login(request, user)


        response = JsonResponse({'code': 0,
                             'message': '注册成功'})

        # 设置 cookie 保存 username 用户名
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        return response

# GET /csrf_token/
class CSRFTokenView(View):
    """csrf跨站请求限制"""
    def get(self, request):
        """获取csrf_token的值"""
        #生成csrf_token的值
        csrf_token = get_token(request)
        #将csrf_token的值返回
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'csrf_token': csrf_token})

# POST /login/
class LoginView(View):
    def post(self, request):
        """用户登录"""
        # 获取参数并进行校验
        # 对json返回数据进行转换
        req_data = json.loads(request.body.decode())
        username = req_data.get('username')
        password = req_data.get('password')
        remember = req_data.get('remember')
        # 1,判断参数完整性
        if not  all([username,password]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        # 2,判断客户端传递的username参数是否符合手机号的格式
        if re.match(r'^1[3-9]\d{9}$', username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        # 3,判断用户名密码是否正确(django框架自带的方法)
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({'code': 400,
                                 'message': '用户名或密码错误'})
        # 保存登录用户的状态
        login(request, user)

        if not remember:
            # 如果未选择记住登录,浏览器关闭即失效
            request.session.set_expiry(0)

        # 返回响应,登录成功
        response = JsonResponse({'code': 0,
                             'message': '登录成功'})

        # 设置 cookie 保存 username 用户名
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        return response

# DELETE /logout/
class LogoutView(View):
    def delete(self, request):
        """退出登录"""
        # 请求登录用户的session的信息
        logout(request)
        # 删除cookie中的username
        request = JsonResponse({'code': 0,
                                'message':'OK'})
        response.delete_cookie('username')

        # 返回响应
        return response

# GET /user/
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        """获取登录用户个人信息"""
        # 获取登录用户对象
        user = request.user
        # 返回响应数据
        info = {
            'username': user.username,
            'mobile': user.mobile,
            'email': user.email,
            'email_active':user.email_active
        }

        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'user': info})

# PUT /user/email/
class UserEmailView(LoginRequiredMixin, View):
    def put(self, request):
        """设置用户的个人邮箱"""
        # 获取参数并进行校验
        req_data = json.loads(request.body.decode())

        email = req_data.get('email')


        if not email:
            return JsonResponse({'code': 400,
                                 'message': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400,
                                 'message': '邮箱参数有误'})
        # 保存用户的个人邮箱设置
        user = request.user
        try:
            user.email = email
            user.save()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '邮箱设置失败'})

        # Celery异步发送邮箱验证邮件
        from celery_tasks.email.tasks import send_verify_email
        verify_url = user.generate_verify_email_url()
        # 发送邮件发送的任务消息
        send_verify_email.delay(email, verify_url)


        # 返回响应
        return JsonResponse({'code': 0,
                             'message': 'OK'})

# PUT /emails/verification/
class EmailVerifyView(View):
    def put(self, request):
        """用户邮箱验证"""
        # 获取加密的用户token并进行校验
        token = request.GET.get('token')

        if not token:
            return JsonResponse({'code': 400,
                                 'message': '缺少token参数'})
        #对用户的信息进行解密
        user = User.check_verify_email_token(token)

        if user is None:
            return JsonResponse({'code': 400,
                                 'message': 'token信息有误'})

        # 设置对应用户的邮箱验证标记为已验证
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '验证邮箱失败'})
        # 返回响应
        return JsonResponse({'code': 0,
                             'message': 'OK'})

# POST /addresses/
class AddressView(LoginRequiredMixin, View):
    def post(self, request):
        """新增用户收货地址"""
        #判断当前用户的收货地址是否超过上限
        try:
            count = Address.objects.filter(user=request.user, is_delete=False).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message':'获取地址数据出错'})
        if count >= 20:
            return JsonResponse({'code': 400,
                                 'message': '收货地址超过上限'})

        # 接收数据并进行数据校验
        req_data = json.loads(request.body.decode())
        title = req_data.get('title')
        receiver = req_data.get('receiver')
        province_id = req_data.get('province_id')
        city_id = req_data.get('city_id')
        district_id = req_data.get('district_id')
        place = req_data.get('place')
        mobile = req_data.get('mobile')
        phone = req_data.get('phone')
        email = req_data.get('email')

        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'message': '参数mobile有误'})

        if phone:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', phone):
                return JsonResponse({'code': 400,
                                     'message': '参数phone有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'message': '参数email有误'})
        # 保存收货地址数据
        try:
            address = Address.objects.create(user=request.user, **req_data)

            # 设置默认收货地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '新增地址保存失败'})
        # 返回响应
        address_data = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'phone': address.phone,
            'email': address.email
        }

        return JsonResponse({'code':0,
                             'message': 'OK',
                             'address': address_data})
    def get(self, request):
        """用户收货地址获取"""
        address_li = []
        try:
            addresses = Address.objects.filter(user=request.user,is_delete=False)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败'})
        # 遍历对象拿出数据,转换成字典,添加到地址列表
        for address in addresses:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'phone': address.email
            }
            address_li.append(address_dict)

        # 返回响应数据
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'default_address_id': request.user.default_address_id,
                             'addresses': address_li})

# PUT/DELETE  /addresses/(?P<address_id>\d+)/
class AddressChangeView(LoginRequiredMixin, View):
    def put(self,request,address_id):
        """修改用户收货地址"""
        try:
            req_data = json.loads(request.body)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '请求参数错误'})

        #传入修改的数据
        receiver = req_data.get('receiver')
        province_id = req_data.get('province_id')
        city_id = req_data.get('city_id')
        district_id = req_data.get('district_id')
        place = req_data.get('place')
        mobile = req_data.get('mobile')
        phone = req_data.get('phone')
        email = req_data.get('email')

        #数据的校验
        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})
        try:
            Area.objects.get(id=province_id)
            Area.objects.get(id=city_id)
            Area.objects.get(id=district_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '地址参数有误'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'message': '手机号格式有误'})
        if phone:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', phone):
                return JsonResponse({'code': 400,
                                     'message': '固定电话格式有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'message': '邮箱格式有误'})
        #对数据库进行修改
        try:
            Address.objects.filter(id=address_id).update(receiver=receiver,
                                                         province_id=province_id,
                                                         city_id=city_id,
                                                         district_id=district_id,
                                                         place=place,
                                                         mobile=mobile,
                                                         phone=phone,
                                                         email=email)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '地址更新失败'})
        #对修改后的地址数据进行展示
        try:
            address = Address.objects.get(id=address_id)
            address_data = {
                'id': address_id,
                'title': address.title,
                'receiver': address.receiver,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'phone': address.phone,
                'email': address.email
            }
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '数据库操作失败'})
        # 返回响应数据
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'address': address_data})
    def delete(self, request,address_id):
        """删除用户收货地址"""
        try:
            Address.objects.filter(id=address_id).update(is_delete=True)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '删除失败'})
        else:
            return JsonResponse({'code': 0,
                                 'message': 'OK'})

# PUT /addresses/(?P<address_id>\d+)/default/
class DefaultAddressView(LoginRequiredMixin, View):
    def put(self,request,address_id):
        """修改默认收货地址"""
        user = request.user
        try:
            user.default_address_id = address_id
            user.save()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '修改默认地址失败'})
        return JsonResponse({'code': 0,
                             'message': 'OK'})

 # PUT /addresses/(?P<address_id>\d+)/title/
class TitleChangeView(LoginRequiredMixin, View):
    def put(self,request, address_id):
        """修改地址标题"""
        req_data = json.loads(request.body)
        title = req_data.get('title')
        if not title:
            return JsonResponse({'code': 400,
                                 'message': '缺少标题参数'})
        try:
            Address.objects.filter(id=address_id).update(title=title)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '修改标题失败'})
        return JsonResponse({'code': 0,
                             'message': 'OK'})

# PUT /password/
class ChangePwdView(LoginRequiredMixin, View):
    def put(self, request):
        """修改用户密码"""
        req_data = json.loads(request.body)
        old_password = req_data.get('old_password')
        new_password = req_data.get('new_password')
        new_password2 = req_data.get('new_password2')

        user = request.user
        username = user.username
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        if not user.check_password(old_password):
            return JsonResponse({'code': 400,
                                 'message': '密码输入错误'})
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                                 'massage': '新密码格式有误'})
        if new_password != new_password2:
            return JsonResponse({'code': 400,
                                 'massage': '两次密码不一致'})
        try:
            user.set_password(new_password)
            user.save()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '设置密码失败'})
        return JsonResponse({'code': 0,
                             'message': 'OK'})

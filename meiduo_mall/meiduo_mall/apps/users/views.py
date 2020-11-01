from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
import json
import re
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from django.middleware.csrf import get_token
from users.models import User
from django.http import JsonResponse, response


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
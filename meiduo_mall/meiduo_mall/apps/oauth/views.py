from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.http import JsonResponse, request
from django.views import  View
# Create your views here.
from django.contrib.auth import login
from oauth.models import OAuthQQUser
from oauth.utils import generate_secret_openid,check_secret_openid
import json
import re
import base64
from django_redis import get_redis_connection
# 获取日志器
import logging

from users.models import User

logger = logging.getLogger('django')
# GET /qq/authorization/
class QQLoginView(View):
    def get(self, request):
        """获取QQ登录地址"""
        next = request.GET.get('next')

        # 创建OAuthQQ对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 获取QQ登录网址并返回
        login_url = oauth.get_qq_url()

        return JsonResponse({'code':0,
                             'message': 'OK',
                             'login_url': login_url})


# /qq/oauth_callback/
class QQUserView(View):
    def get(self, request):
        """
        获取 QQ 登录用户的openid并进行处理：
        ① 获取 code 并进行校验(code必须传)
        ② 根据 code 请求 QQ 平台获取 access_token
        ③ 根据 access_token 请求 QQ 平台获取 openid
        ④ 根据 openid 判断 QQ 登录用户和本网站用户是否进行了绑定
            a. 如果未绑定，将 openid 加密进行返回
            b. 如果已绑定，让对应的用户登录成功，返回响应
        """
        # 1,获取code并进行校验
        code = request.GET.get('code')

        if code is None:
            return JsonResponse({'code':400,
                                 'message': '缺少code参数'})
        try:
            # 2,根据code请求QQ平台获取access_token
            oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                            client_secret=settings.QQ_CLIENT_SECRET,
                            redirect_uri=settings.QQ_REDIRECT_URI)
            access_token = oauth.get_access_token(code)
            # 根据access_token获取open_id
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'message': 'QQ登录失败'})
        # 根据openid判断 QQ 登录用户和本站用户是否进行绑定
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果未进行绑定,将openid加密进行返回
            secret_openid = generate_secret_openid(openid)
            return JsonResponse({'code': 300,
                                 'message': 'OK',
                                 'secret_openid':secret_openid})
        else:
            # 如果已经绑定, 保存用户登录状态
            user = qq_user.user
            login(request, user)

            reponse = JsonResponse({'code': 0,
                                    'message': 'OK'})
            # 设置cookie
            reponse.set_cookie('username', user.username,
                               max_age=3600 * 24 * 14)
            return reponse

    # POST /qq/oauth_callback/
    def post(self,request):
        """
        保存 QQ 登录用户绑定的数据：
        ① 获取参数并进行校验
        ② 保存 QQ 登录用户绑定的数据
        ③ 返回响应，登录成功
        """
        # 1,获取参数并进行校验
        req_data = json.loads(request.body)
        mobile = req_data.get('mobile')
        password = req_data.get('password')
        sms_code = req_data.get('sms_code')
        secret_openid = req_data.get('secret_openid')
        # 2,校验参数
        # 1),参数的完整性
        if not all([mobile,password,sms_code,secret_openid]):
            return JsonResponse({'code':400,
                                 'message':'缺少必传参数'})
        # 2)判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'message': '请输入正确的手机号码'})
        # 3)判断密码是否合格
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'message': '请输入8-20位的密码'})
        # 4)短信验证码是否正确
        redis_conn = get_redis_connection('verify_code')
        sms_code_redis = redis_conn.get('sms_%s' % mobile)

        if not sms_code_redis:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码已过期'})
        if sms_code != sms_code_redis:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码错误'})
        # 尝试对secret_openid进行解密
        openid = check_secret_openid(secret_openid)

        if openid is None:
            return JsonResponse({'code': 400,
                                 'message': 'openid信息有误'})

        # 根据mobile去查询用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 绑定用户不存在, 添加一个新的用户
            username = base64.b64encode(mobile.encode()).decode()
            user = User.objects.create_user(username=username,
                                            mobile=mobile,
                                            password=password)
        else:
            # 绑定用户存在,需要进行密码的校验
            if not user.check_password(password):
                return JsonResponse({'code': 400,
                                     'message': '账户密码有误'})
        # 保存QQ登录用户绑定的数据
        try:
            # OAuthQQUser.objects.create(openid=openid, user=user)
            OAuthQQUser.objects.create(openid=openid, user_id=user.id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '保存绑定数据失败'})

        # ③ 返回响应，登录成功
        # 保存登录用户的信息
        login(request, user)

        response = JsonResponse({'code': 0,
                                 'message': 'OK'})

        # 设置 cookie 中保存 username
        response.set_cookie('username', user.username, 3600 * 24 * 14)
        return response
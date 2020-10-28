from django.shortcuts import render

# Create your views here.
from django.views import View
from users.models import User
from django.http import JsonResponse


class UsernameCountView(View):
    def get(self,request,username):
        """判断注册用户名是否重复"""
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败!'})
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'count': count})

class MobileCountView(View):
    def get(self,request,mobile):
        """判断注册用户名是否重复"""
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败!'})
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'count': count})


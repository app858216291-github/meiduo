from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.views import View

from meiduo_mall.meiduo_mall.libs.captcha.captcha import captcha


class ImageCodeView(View):
    """获取图片验证码数据"""
    def get(self, request, uuid):
        """图片验证码的生成"""
        #1,生成验证码图片
        text,image = captcha.generate_captcha()
        #2,保存验证码图片上的文本
        #3,将验证码进行返回
        return HttpResponse(image, content_type='image/jpg')

from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
import random
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import send_sms_code

#获取日志器
import logging

logger = logging.getLogger('django')


class ImageCodeView(View):
    """获取图片验证码数据"""
    def get(self, request, uuid):
        """图片验证码的生成"""
        #1,生成验证码图片
        text,image = captcha.generate_captcha()
        #2,保存验证码图片上的文本
        redis_conn = get_redis_connection('verify_code')
        redis_conn.set('img_%s' % uuid, text, 300)
        #3,将验证码进行返回
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """获取短信验证码"""
    def get(self,request,mobile):
        #判断短信是否60s内重复
        redis_conn = get_redis_connection('verify_code')

        send_flag = redis_conn.get('send_flag_%s' % mobile)

        if send_flag:
            #说明60s之内发过短信,不再重复发
            return JsonResponse({'code': 400,
                                 'message': '短信验证码发送过于频繁'})
        #用户输入的图片验证码
        image_code = request.GET.get('image_code')
        #图片验证码标记:uuid
        uuid = request.GET.get('image_code_id')

        if not all([image_code,uuid]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        #获取redis里的图片验证码
        redis_conn = get_redis_connection('verify_code')

        # 对比用户输入图片验证码是否正确
        try:
            real_image_code = redis_conn.get('img_%s' % uuid)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '获取图片验证码出错!'})
        # 判断验证码是否失效
        if real_image_code is None:
            return JsonResponse({'code': 400,
                                 'message': '图片验证码失效'})
        #删除图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            # 记录日志
            logger.error(e)

        #对比图形验证码,不区分大小写
        if image_code.lower() != real_image_code.lower():
            return JsonResponse({'code': 400,
                                 'message': '输入图形验证码有误'})
        #生成保存并发送短信验证码
        sms_code = '%06d' % random.randint(0,999999)

        logger.info('短信验证码为: %s' % sms_code)
        # # 保存短信验证码
        # redis_conn.set('sms_%s' % mobile ,sms_code, 300)
        # # 设置短信发送的标记，有效期为：60s
        # redis_conn.set('send_flag_%s' % mobile, 1, 60)
        # 设计redis pipeline管道优化
        try:
            pl = redis_conn.pipeline()
            pl.set('sms_%s' % mobile ,sms_code, 300)
            pl.set('send_flag_%s' % mobile, 1, 60)
            pl.execute()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'mesage': '保存短信验证码出错'})
        # 发送短信验证码
        # CCP().send_template_sms(mobile,[sms_code,5], 1)
        #发出发送短信的任务消息,SMSCodeView的作用是生产者
        send_sms_code.delay(mobile, sms_code)

        # 返回响应
        return JsonResponse({'code': 0,
                             'message': '发送短信成功'})
import os

from alipay import AliPay
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from meiduo_mall.utils.mixins import LoginRequiredMixin

from orders.models import OrderInfo


# /payment/(?P<order_id>\d+)/
class PaymentURLView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        """获取支付宝支付地址"""
        # 获取参数并进行校验
        user = request.user

        try:
            order = OrderInfo.objects.get(user=user,
                                          order_id=order_id,
                                          status=1)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '订单信息有误'})

        # 生成支付宝支付地址并返回
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'keys/app_private_key.pem'),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type='RSA2',
            debug=settings.ALIPAY_DEBUG
        )
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'alipay_url': alipay_url})
from decimal import Decimal

from django.http import JsonResponse
from django.views import View
from meiduo_mall.utils.mixins import LoginRequiredMixin

from carts.utils import CartHelper
from goods.models import SKU
from users.models import Address

from django.utils import timezone
from django.db import transaction

from orders.models import OrderInfo, OrderGoods
import json

# GET /orders/settlement/
class OrderSettlementView(LoginRequiredMixin, View):
    def get(self, request):
        """订单结算页面"""
        # 获取当前用户的收获地址
        addresses = Address.objects.filter(user=request.user, is_delete=False)

        # 从 redis 中获取用户所要结算的商品信息
        try:
            cart_helper = CartHelper(request)
            cart_dict = cart_helper.get_redis_selected_cart()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '获取购物车数据失败'})

        # 查询数据库获取对应的商品数据
        sku_li = []
        try:
            skus = SKU.objects.filter(id__in=cart_dict.keys())

            for sku in skus:
                sku_li.append({
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': 'http://192.168.19.131:8888/' + sku.default_image.name,
                    'price': sku.price,
                    'count': cart_dict[sku.id]
                })
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '获取商品数据失败'})

        # 订单运费
        freight = Decimal(10.00)

        # 地址信息
        address_li = []

        try:
            for address in addresses:
                address_li.append({
                    'id': address.id,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'receiver': address.receiver,
                    'mobile': address.mobile,
                })
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '地址信息获取有误'})

        # 组织并返回响应数据
        context = {
            'addresses': address_li,
            'skus': sku_li,
            'freight': freight,
            'nowsite': request.user.default_address_id
        }

        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'context': context})


# POST /orders/commit/
class OrderCommitView(LoginRequiredMixin, View):
    def post(self, request):
        """订单创建"""
        # 获取参数并进行校验
        req_data = json.loads(request.body.decode())
        address_id = req_data.get('address_id')
        pay_method = req_data.get('pay_method')

        # 校验参数的完整性
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})
        # 判断地址是否存在
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '地址信息有误'})
        # 1,货到付款, 2, 支付宝
        if pay_method not in [1, 2]:
            return JsonResponse({'code': 400,
                                 'message': '支付方式有误'})
        # 组织订单数据,生成订单
        user = request.user
        order_id = 'E' + timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        # total_count 商品总数 total_amount  订单总金额
        total_count = 0
        total_amount = 0

        # 订单状态
        if pay_method == 1:
            # 货到付款, 订单状态: 待发货
            status = 2
        else:
            # 支付宝, 订单状态: 待支付
            status = 1

        # 运费(此处固定)
        freight = Decimal(10.00)

        with transaction.atomic():
            # 设置数据库操作时,事务中的保存点
            sid = transaction.savepoint()

            # 向 tb_order_info 数据表里添加一行记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             address=address,
                                             total_count=total_count,
                                             total_amount=total_amount,
                                             freight=freight,
                                             pay_method=pay_method,
                                             status=status)
            # 遍历用户要购买的商品记录, 循环向 tb_order_goods 表里添加记录
            cart_helper = CartHelper(request)
            cart_dict = cart_helper.get_redis_selected_cart()
            sku_ids = cart_dict.keys()

            for sku_id in sku_ids:
                for i in range(3):
                    sku = SKU.objects.get(id=sku_id)
                    count = cart_dict[sku_id]

                    # 记录原始库存和销量
                    origin_stock = sku.stock
                    origin_sales = sku.sales

                    # 判断库存是否充足
                    if count > sku.stock:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'code': 400,
                                             'message': '商品库存不足'})
                    # # 减少sku商品库存,增加销量
                    # sku.stock -= count
                    # sku.sales += count
                    # sku.save()

                    # 进行休眠操作, 让CPU调度其它进程或线程,模拟订单并发问题
                    import time
                    time.sleep(10)

                    # 更新商品库存和销量
                    new_stock = origin_stock - count
                    news_sales = origin_sales + count

                    # 注意: update 方法返回的是被更新的行数
                    res = SKU.objects.filter(id=sku_id,
                                             stock=origin_stock).updatea(stock=new_stock,
                                                                         sales=news_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试下单更新三次,仍然失败,提示报错
                            # 数据库操作时,撤销事务中指定保存点之后的操作
                            transaction.savepoint_rollback(sid)
                            return JsonResponse({'code': 400,
                                                 'message': '下单失败'})
                        # 更新失败,重新进行尝试
                        continue
                    # 增加对应spu商品的销量
                    sku.spu.sales += count
                    sku.spu.save()
                    # 保存订单商品信息
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)
                    # 更新成功,跳出循环
                    break


                # 累加计算订单商品的总数量和价格
                total_count += count
                total_amount += count * sku.price

        total_amount += freight
        order.total_count = total_count
        order.total_amount = total_amount
        order.save()

        # 清除用户购物车中已购买的记录
        cart_helper.clear_redis_selected_cart()

        # 返回响应
        return JsonResponse({'code': 0,
                             'message': '下单成功',
                             'order_id': order_id})
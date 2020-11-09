import json,base64,pickle
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from goods.models import SKU

# Create your views here.
redis_conn = get_redis_connection('cart')



# POST /carts/
class CartsView(View):
    def post(self, request):
        """添加购物车数据"""
        # 接收参数
        req_data = json.loads(request.body)
        sku_id = req_data.get('sku_id')
        count = req_data.get('count')
        selected = req_data.get('selected', True)

        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400,
                                 'message': '参数sku_id有误'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '参数count错误'})
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'message': '参数selected有误'})


        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 如果已经登录,redis
            try:
                # 管道优化
                pl = redis_conn.pipeline()
                #hincrby:哈希增量方法
                pl.hincrby('cart_%s' % user.id, sku_id, count)

                #保存商品被勾选状态 set方法 sadd
                if selected:
                    pl.sadd('cart_selected_%s' % user.id, sku_id)
                pl.execute()
            except Exception as e:
                return JsonResponse({'code': 400,
                                     'message': '操作数据库失败'})
            return JsonResponse({'code': 0,
                                 'message': 'OK',
                                 'count': count})

        else:
            # 如果未登录,cookie
            # 获取cookie里的购物车数据,并判断是否有数据
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)

            else:
                cart_dict = {}
            # 判断cookie里是否有数据
            if sku_id in cart_dict:
                # 购物车已存在,做增量计算
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {'count': count,
                                 'selected': selected}
            # 将原始的购物车数据进行编码
            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_carts_str = cart_str_bytes.decode()
            # cookie_carts_str = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 将新的购物车数据写入cookie
            response = JsonResponse({'code': 0,
                                     'message': 'OK',
                                     'count': count})
            response.set_cookie('cart', cookie_carts_str, 3600 * 24 * 14)

            return response
    def get(self,request):
        """获取购物车数据"""
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录,,获取redis数据
            # hash哈希数据获取
            redis_dict_cart = redis_conn.hgetall('cart_%s' % user.id)
            # set集合数据获取
            redis_set_selected= redis_conn.smembers('cart_selected_%s' % user.id)
            # 将hash和set数据合并
            cart_dict = {}
            for sku_id, count in redis_dict_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_set_selected
                }

        else:
            # 用户未登录,获取cookie数据
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
                # cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                print(cart_dict)
            else:
                cart_dict = {}
        # 构造响应数据
        # 获取字典中所有的Key.(sku_id)
        sku_ids = cart_dict.keys()
        # for sku_id in sku_ids:
        #     sku = SKU.objects.get(id=sku_id)
        # 一次性查询到所有的skus
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': 'http://192.168.19.131:8888/' + sku.default_image.name,
                'count': int(cart_dict[sku.id]['count']),
                'selected': cart_dict[sku.id]['selected'],
                # 'amount': str(sku.price * cart_dict[sku_id]['count'])
            })
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'cart_skus': cart_skus})
    def put(self,request):
        """修改购物车数据"""
        # 接收参数
        req_data = json.loads(request.body.decode())
        sku_id = req_data.get('sku_id')
        count = req_data.get('count')
        selected = req_data.get('selected', True)
        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400,
                                 'message': '参数sku_id有误'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '参数count错误'})
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'message': '参数selected有误'})
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 如果已经登录,redis
            try:
                # 管道优化
                pl = redis_conn.pipeline()
                # 直接使用传来的数据覆盖
                pl.hset('cart_%s' % user.id, sku_id, count)
                #修改商品被勾选状态 set方法 sadd
                if selected:
                    pl.sadd('cart_selected_%s' % user.id, sku_id)
                else:
                    pl.srem('cart_selected_%s' % user.id, sku_id)
                # 管道执行
                pl.execute()
            except Exception as e:
                return JsonResponse({'code': 400,
                                     'message': '操作数据库失败'})
            else:
                return JsonResponse({'code': 0,
                                     'message': 'OK'})
        else:
            # 如果未登录,cookie
            # 获取cookie里的购物车数据,并判断是否有数据
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
            if sku_id in cart_dict:
                # 覆盖写入
                cart_dict[sku_id] = {'count': count,
                                     'selected': selected}
            else:
                return JsonResponse({'code': 400,
                                     'message': '修改购物车失败'})
            # 将原始的购物车数据进行编码
            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_carts_str = cart_str_bytes.decode()
            cart_sku = {
                'sku': sku_id,
                'count': count,
                'selected': selected,
            }

            # 将新的购物车数据写入cookie
            response = JsonResponse({'code': 0,
                                     'message': 'OK',
                                     'cart_sku': cart_sku})
            response.set_cookie('cart', cookie_carts_str, 3600 * 24 * 14)

            return response

    def delete(self, request):
        """删除购物车信息"""
        # 获取商品的id
        req_data = json.loads(request.body.decode())
        sku_id = req_data.get('sku_id')

        # 校验商品id
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400,
                                 'message': '参数sku_id有误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 如果已经登录, redis
            try:
                # 管道优化
                pl = redis_conn.pipeline()
                #hincrby:哈希增量方法
                pl.hdel('cart_%s' % user.id, sku_id)
                pl.sadd('cart_selected_%s' % user.id, sku_id)
                pl.execute()
            except Exception as e:
                return JsonResponse({'code':400,
                                     'message': '操作数据库失败'})
            return JsonResponse({'code': 0,
                                 'message': '删除数据成功'})
        else:
            # 用户未登录,cookie
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)

            else:
                cart_dict = {}
            # 判断cookie里是否有数据
            if sku_id in cart_dict:
                del cart_dict[sku_id]
            else:
                return JsonResponse({'code': 400,
                                     'message': '删除数据失败'})
            # 将原始的购物车数据进行编码
            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_carts_str = cart_str_bytes.decode()

            # 将新的购物车数据写入cookie
            response = JsonResponse({'code': 0,
                                     'message': '删除数据成功'})
            response.set_cookie('cart', cookie_carts_str, 3600 * 24 * 14)


# carts / selection /
class ALLChoseView(View):
    def put(self, request):
        """购物车商品全选"""
        # 获取商品信息
        req_data = json.loads(request.body.decode())
        selected = req_data.get('selected')
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'message': '参数selected有误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 如果已经登录,redis
            if selected:
                try:
                    # 管道优化
                    pl = redis_conn.pipeline()
                    # 直接使用传来的数据覆盖
                    pl.hkeys('cart_%s' % user.id)
                    # 修改商品被勾选状态 set方法 sadd
                    for sku_id in pl:
                        pl.sadd('cart_selected_%s' % user.id, sku_id)
                    # 管道执行
                    pl.execute()
                except Exception as e:
                    return JsonResponse({'code': 400,
                                         'message': '操作数据库失败'})
            else:
                try:
                    # 管道优化
                    pl = redis_conn.pipeline()
                    # 直接使用传来的数据覆盖
                    pl.hkeys('cart_%s' % user.id)
                    # 修改商品被勾选状态 set方法 sadd
                    for sku_id in pl:
                        pl.srem('cart_selected_%s' % user.id, sku_id)
                except Exception as e:
                    return JsonResponse({'code': 400,
                                         'message': '操作数据库失败'})

            return JsonResponse({'code': 0,
                                 'message': 'OK'})
        else:
            # 用户未登录
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected
                response = JsonResponse({'code': 0,
                                         'message': 'OK'})
                cart_dict_bytes = pickle.dumps(cart_dict)
                cart_str_bytes = base64.b64encode(cart_dict_bytes)
                cookie_carts_str = cart_str_bytes.decode()
                response.set_cookie('cart', cookie_carts_str, 3600 * 24 * 14)
                return response
            else:
                return JsonResponse({'code': 400,
                                     'message': '购物车中没有记录'})
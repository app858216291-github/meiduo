import json

from django.http import JsonResponse
from django.views import View

from carts.utils import CartHelper
from goods.models import SKU


# /cart/
class CartView(View):
    def post(self, request):
        """
        购物车数据新增：
        ① 获取参数并进行校验
        ② 根据用户是否登录，分别进行购物车数据的保存
        ③ 返回响应，购物车记录添加成功
        """
        # ① 获取参数并进行校验
        req_data = json.loads(request.body)
        sku_id = req_data.get('sku_id')
        count = req_data.get('count')
        selected = req_data.get('selected', True)

        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': 'count参数有误'})

        if count <= 0:
            return JsonResponse({'code': 400,
                                 'message': 'count参数有误'})

        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': 'sku商品不存在'})

        # ② 根据用户是否登录，分别进行购物车数据的保存
        response = JsonResponse({'code': 0,
                                 'message': '购物车添加成功',
                                 'count': count})

        try:
            cart_helper = CartHelper(request, response)
            cart_helper.add_cart(sku_id, count, selected)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '购物车添加失败'})

        # ③ 返回响应，购物车记录添加成功
        return response

    def get(self, request):
        """
        购物车记录获取：
        ① 根据用户是否登录，分别进行购物车数据的获取
        ② 组织数据并返回响应
        """
        # ① 根据用户是否登录，分别进行购物车数据的获取
        try:
            cart_helper = CartHelper(request)
            cart_dict = cart_helper.get_cart()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '购物车获取失败'})

        # ② 组织数据并返回响应
        try:
            skus = SKU.objects.filter(id__in=cart_dict.keys())
        except Exception:
            return JsonResponse({'code': 400,
                                 'message': '获取sku商品信息失败'})

        cart_skus = []

        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': 'http://192.168.19.131:8888/' + sku.default_image.name,
                'count': cart_dict[sku.id]['count'],
                'selected': cart_dict[sku.id]['selected'],
            })

        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'cart_skus': cart_skus})

    def put(self, request):
        """
        购物车记录修改：
        ① 获取参数并进行校验
        ② 根据用户是否登录，分别修改购物车记录的数据
        ③ 返回响应
        """
        # ① 获取参数并进行校验
        req_data = json.loads(request.body)
        sku_id = req_data.get('sku_id')
        count = req_data.get('count')
        selected = req_data.get('selected', True)

        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': 'count参数有误'})

        if count <= 0:
            return JsonResponse({'code': 400,
                                 'message': 'count参数有误'})

        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': 'sku商品不存在'})

        # ② 根据用户是否登录，分别修改购物车记录的数据
        cart_sku = {
            'sku_id': sku_id,
            'count': count,
            'selected': selected
        }

        response = JsonResponse({'code': 0,
                                 'message': '购物车记录修改成功',
                                 'cart_sku': cart_sku})

        try:
            cart_helper = CartHelper(request, response)
            cart_helper.update_cart(sku_id, count, selected)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '购物车记录修改失败'})

        return response

    def delete(self, request):
        """
        购物车记录删除：
        ① 获取参数并进行校验
        ② 根据用户是否登录，删除对应的购物车记录
        ③ 返回响应
        """
        # ① 获取参数并进行校验
        req_data = json.loads(request.body)
        sku_id = req_data.get('sku_id')

        if not sku_id:
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        # ② 根据用户是否登录，删除对应的购物车记录
        response = JsonResponse({'code': 0,
                                 'message': '购物车记录删除成功'})

        try:
            cart_helper = CartHelper(request, response)
            cart_helper.remove_cart(sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '购物车记录删除失败'})

        # ③ 返回响应
        return response


# PUT /carts/selection/
class CartSelectView(View):
    def put(self, request):
        """
        购物车记录全选和取消全选：
        ① 获取参数并进行校验
        ② 根据用户是否登录，对购物车记录进行全选和取消全选操作
        ③ 返回响应
        """
        # ① 获取参数并进行校验
        req_data = json.loads(request.body)
        selected = req_data.get('selected', True)

        # ② 根据用户是否登录，对购物车记录进行全选和取消全选操作
        response = JsonResponse({'code': 0,
                                 'message': '购物车记录操作成功'})
        try:
            cart_helper = CartHelper(request, response)
            cart_helper.select_cart(selected)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '购物车记录操作失败'})

        # ③ 返回响应
        return response

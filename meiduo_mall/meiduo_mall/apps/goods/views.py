from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from goods.models import GoodsCategory, SKU
from goods.utils import get_breadcrumb

# GET /list/(?P<category_id>\d+)/skus/
class SKUListView(View):
    def get(self, request, category_id):
        """分类商品数据获取"""
        # 获取对应的参数：page、page_size、ordering
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 5)
        ordering = request.GET.get('ordering', '-create_time')

        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400,
                                 'message': '分类不存在'})

        # 查询分类SKU商品的相关数据
        # 面包屑导航数据
        try:
            breadcrumb = get_breadcrumb(cat3)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '获取面包屑导航数据出错'})
        # 分类SKU商品数据
        try:
            skus = SKU.objects.filter(category_id=category_id,
                                      is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '获取分类商品数据出错'})

        # 对分类SKU商品数据进行分页
        from django.core.paginator import Paginator
        # 创建一个 paginator 类的对象, paginator('要分页数据','页容量')
        # paginator.num_pages: 分页之后的总页数
        paginator = Paginator(skus, page_size)
        # 获取某一页的数据: get_page(页码), 返回的是一个page类的对象
        results = paginator.get_page(page)

        sku_li = []
        for sku in results:
            sku_data = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'comments': sku.comments,
                'default_image_url': 'http://192.168.19.131:8888/' + sku.default_image.name
            }

            sku_li.append(sku_data)

        # 返回响应数据
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'breadcrumb': breadcrumb,
                             'list': sku_li,
                             'count': paginator.num_pages})
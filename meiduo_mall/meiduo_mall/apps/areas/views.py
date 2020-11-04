from django.core.cache import cache

from django.shortcuts import render
from django.http import JsonResponse
# Create your views here.
from django.views import View

from areas.models import Area

# GET /areas/
class ProvinceAreasView(View):
    def get(self, request):
        """获取所有省级地区信息"""
        #查询数据库获取所有省级地区信息
        # 当用户发送请求时,尝试从缓存中获取对应的数据
        cache_provinces = cache.get('provinces')

        if not cache_provinces:
            #缓存中没有数据
            # 查询数据库获取所有省级地区的数据
            try:
                provinces = Area.objects.filter(parent=None).values('id', 'name')
                #将 QuerySet 数据转成 list
                provinces = list(provinces)

                # 将provinces在缓存中存储一份
                cache.set('provinces', provinces, 3600)
            except Exception as e:
                return JsonResponse({'code': 400,
                                     'message': '获取地区出错'})
        else:
            #缓存中有数据
            provinces = cache_provinces

            # 组织数据进行返回
            return JsonResponse({'code': 0,
                                 'message': 'OK',
                                 'provinces': provinces})

# GET /areas/(?P<pk>\d+)/
class SubAreasView(View):
    def get(self, request, pk):
        """获取指定地区的下级数据"""
        #尝试先从缓存中获取数据
        cache_sub_areas = cache.get('sub_areas_%s' % pk)
        if not cache_sub_areas:
            #缓存中没有数据
            # 根据 pk 查询这个地区的下级地区的数据
            try:
                sub_areas = Area.objects.filter(parent=pk).values('id', 'name')
                # 将 Queryset 数据转换成list
                sub_areas = list(sub_areas)
                # 将sub_areas在缓存中存储一份
                cache.set('sub_areas_%s' % pk, sub_areas, 3600)
            except Exception as e:
                return JsonResponse({'code': 400,
                                     'message': '获取地区出错'})
        else:
            #缓存中有数据:
            sub_areas = cache_sub_areas

        # 组织数据返回
        return JsonResponse({'code': 0,
                             'message': 'Ok',
                             'subs': sub_areas})
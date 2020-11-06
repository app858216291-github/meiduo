import sys

# 将当前目录的上级目录添加到python搜索包路径列表当中
# 否则'meiduo_mall.settings.dev'会找不到
sys.path.insert(0, '../')

import os
# 设置django运行所依赖的环境变量
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','meiduo_mall.settings.dev')


# django 环境进行初始化操作
import django
django.setup()

from django.conf import settings
from django.template import loader

from goods.models import SKU
from goods.utils import get_categories, get_goods_and_spec

def generate_static_sku_detail_html(sku_id):
    """生成指定sku商品的静态详细页面"""
    # 获取数据
    categories = get_categories()
    spu, specs, sku = get_goods_and_spec(sku_id)

    # 加载模块文件并进行渲染
    context = {
        'categories': categories,
        'goods': spu,
        'specs': specs,
        'sku': sku,
        'nginx_url': "http://192.168.19.131:8888/"
    }

    template = loader.get_template('detail.html')
    static_html = template.render(context)

    # 写入静态文件
    save_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'goods/%s.html' % sku_id)
    with open(save_path, 'w', encoding='utf8') as f:
        f.write(static_html)


if __name__ == '__main__':
    # 获取所有sku商品的id
    skus = SKU.objects.values('id').order_by('id')

    iterator = skus.iterator(chunk_size=10)

    for sku in iterator:
        print(sku['id'])
        generate_static_sku_detail_html(sku['id'])
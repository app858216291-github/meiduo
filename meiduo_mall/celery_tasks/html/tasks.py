import os

from django.conf import settings
from django.template import loader

from celery_tasks.main import celery_app
from goods.utils import get_categories, get_goods_and_spec

@celery_app.tasks(name='generate_static_sku_detail_html')
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
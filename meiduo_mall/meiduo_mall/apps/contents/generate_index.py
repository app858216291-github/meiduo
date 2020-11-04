import os
from collections import OrderedDict
from django.conf import settings
from goods.models import GoodsChannel
from contents.models import ContentCategory,Content
from django.template import loader


def generate_static_index_html():
    """网页首页静态化"""
    print('---generate_static_index_html---')
    # 查新数据库获取静态化首页所需的数据
    # OrderedDict:有序列表
    categories = OrderedDict({})
    channels = GoodsChannel.objects.order_by('group_id','sequence') # QuerySet

    for channel in channels:
        # 获取 channel 频道频道组id
        group_id = channel.group_id

        if group_id not in categories:
            categories[group_id]={'channel': [],
                                  'sub_cats': []}
        # 查询 channel 关联的 一级分类
        cat1 = channel.category
        categories[group_id]['channels'].append({'id': cat1.id,
                                                 'name': cat1.name,
                                                 'url': channel})
        # 查询一级分类下面的二级分类
        cat2s = cat1.subs.all()
        for cat2 in cat2s:
            cat2.sub_cats = []
            # 查询二级分类下面的三级分类
            cat3s = cat2.subs.all()
            for cat3 in cat3s:
                cat2.sub_cats.append(cat3)

            categories[group_id]['sub_cats'].append(cat2)

    # 首页广告数据查询
    contents = {}
    content_cats = ContentCategory.objects.all()

    for cat in content_cats:
        contents[cat.key] = Content.objects.filter(category=cat,
                                                   status=True).order_by('sequence')
    # 将查到的数据传递给模版文件, 进行模版渲染
    context = {'categories': categories,
               'contents': contents,
               'nginx_url': 'http://192.168.19.131:8888'}
    # 加载模版
    template = loader.get_template('index.html')
    static_html = template.render(context=context)

    # 将渲染生成的完整 html 内容保存成一个静态页面
    save_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')

    with open(save_path, 'w', encoding='utf8') as f:
        f.write(static_html)
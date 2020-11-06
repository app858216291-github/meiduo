import copy
from collections import OrderedDict
from goods.models import GoodsChannel, SKU, SKUImage, SKUSpecification, SPUSpecification, SpecificationOption


def get_breadcrumb(cat3):
    """面包屑导航数据获取"""
    # 查询二级分类和一级分类
    cat2 = cat3.parent
    cat1 = cat2.parent

    # 组织面包屑导航数据
    breadcrumb = {
        'cat1': cat1.name,
        'cat2': cat2.name,
        'cat3': cat3.name
    }

    return breadcrumb

def get_categories():
    """商品分类数据获取"""
    categories = OrderedDict()
    channels = GoodsChannel.objects.order_by('group_id','sequence')

    for channel in channels:
        group_id = channel.group_id

        if group_id not in categories:
            categories[group_id]={
                'channels': [],
                'sub_cats': []
            }

        # 获取频道对应的一级分类
        cat1 = channel.category

        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 获取一级分类的下级分类(二级分类)
        cat2s = cat1.subs.all()
        for cat2 in cat2s:
            cat2.sub_cats = []

            # 获取二级分类的下级分类(三级分类)
            cat3s = cat2.subs.all()
            for cat3 in cat3s:
                cat2.sub_cats.append(cat3)

            categories[group_id]['sub_cats'].append(cat2)

    return categories


def get_goods_and_spec(sku_id):
    """获取指定sku商品的信息"""
    # 获取SKU商品数据
    sku = SKU.objects.get(id=sku_id)

    # 获取SKU商品的图片数据
    sku.images = SKUImage.objects.filter(sku=sku)

    # 获取SKu商品的具体规格信息数据
    # ["规格1-选项ID", "规格2-选项ID", ...]
    keys = []
    sku_specs = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')

    for sku_spec in sku_specs:
        keys.append(sku_spec.option_id)

    # 获取 SKU 商品所属的 SPU 数据
    spu = sku.spu

    # 获取该 SPU 下的所有 SKU 商品数据
    spu_skus = SKU.objects.filter(spu=spu, is_launched=True)

    # 获取该 SPU 下的所有 SKU 商品的规格选项与 SKU 商品的对应关系
    # {
    #     ('规格1-选项a', '规格2-选项b', ..): 'SKU商品ID',
    #     ...
    # }
    skus_dict = {}

    for temp_sku in spu_skus:
        sku_specs = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')

        temp_keys = []
        for sku_spec in sku_specs:
            temp_keys.append(sku_spec.option_id)

        skus_dict[tuple(temp_keys)] = temp_sku.id

    # 在其他规格选项不变的情况下,遍历在每个选项上绑定对应的 SKU 商品的 ID
    spu_specs = SPUSpecification.objects.filter(spu=spu).order_by('id')
    for index, spu_spec in enumerate(spu_specs):
        # 获取该规格下的所有选项数据
        spec_optins = SpecificationOption.objects.filter(spec=spu_spec)

        temp_keys = copy.deepcopy(keys)

        for spec_optin in spec_optins:
            temp_keys[index] = spec_optin.id
            spec_optin.sku_id = skus_dict.get(tuple(temp_keys))

        spu_spec.spec_options = spec_optins
    return  spu, spu_specs ,sku
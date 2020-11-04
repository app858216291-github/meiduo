from django.db import models

from meiduo_mall.utils.base_model import BaseModel


class Brand(BaseModel):
    """品牌模型"""
    # 品牌名称
    name = models.CharField(max_length=20,
                            verbose_name='名称')
    # 品牌logo
    logo = models.ImageField(verbose_name='Logo图片')
    # 品牌首字母
    first_letter = models.CharField(max_length=1,
                                    verbose_name='品牌首字母')

    class Meta:
        db_table = 'tb_brand'
        verbose_name = '品牌'

    def __str__(self):
        return self.name


class GoodsCategory(BaseModel):
    """商品分类模型：自关联"""
    # 分类的名称
    name = models.CharField(max_length=10, verbose_name='名称')
    # 分类的上级id (分类一共有三级)
    parent = models.ForeignKey('self',
                               null=True,
                               blank=True,
                               related_name="subs",
                               on_delete=models.CASCADE,
                               verbose_name='父类别')

    class Meta:
        db_table = 'tb_goods_category'
        verbose_name = '商品类别'

    # 返回分类名称
    def __str__(self):
        return self.name


class GoodsChannel(BaseModel):
    """商品频道模型"""
    # 当前商品频道属于哪个组
    group_id = models.IntegerField(verbose_name='组号')
    # 频道对应的一级分类id
    category = models.ForeignKey(GoodsCategory,
                                 on_delete=models.CASCADE,
                                 verbose_name='一级商品类别')
    # 当前频道点击后跳转的页面地址
    url = models.CharField(max_length=50,
                           verbose_name='频道页面地址')
    # 同组频道展示顺序
    sequence = models.IntegerField(verbose_name='组内顺序')

    class Meta:
        db_table = 'tb_goods_channel'
        verbose_name = '商品频道'

    def __str__(self):
        return self.category.name


class SPU(BaseModel):
    """SPU商品模型"""
    # SPU商品名称
    name = models.CharField(max_length=50, verbose_name='名称')
    # SPU商品所属品牌
    brand = models.ForeignKey(Brand,
                              on_delete=models.PROTECT,
                              verbose_name='品牌')
    # SPU商品所属一级分类
    category1 = models.ForeignKey(GoodsCategory,
                                  on_delete=models.PROTECT,
                                  related_name='cat1_spu',
                                  verbose_name='一级分类')
    # SPU商品所属二级分类
    category2 = models.ForeignKey(GoodsCategory,
                                  on_delete=models.PROTECT,
                                  related_name='cat2_spu',
                                  verbose_name='二级分类')
    # SPU商品所属三级分类
    category3 = models.ForeignKey(GoodsCategory,
                                  on_delete=models.PROTECT,
                                  related_name='cat3_spu',
                                  verbose_name='三级分类')
    # SPU商品总销量
    sales = models.IntegerField(default=0,
                                verbose_name='总销量')
    # SPU商品总评价
    comments = models.IntegerField(default=0,
                                   verbose_name='总评价')
    desc_detail = models.TextField(default='',
                                   verbose_name='详细介绍')
    desc_pack = models.TextField(default='',
                                 verbose_name='包装信息')
    desc_service = models.TextField(default='',
                                    verbose_name='售后服务')

    class Meta:
        db_table = 'tb_spu'
        verbose_name = '商品'

    def __str__(self):
        return self.name


class SKU(BaseModel):
    """商品SKU模型"""
    # SKU商品名称
    name = models.CharField(max_length=50,
                            verbose_name='名称')
    # SKU商品副标题
    caption = models.CharField(max_length=100,
                               verbose_name='副标题')
    # 这个SKU商品属于哪个SPU
    spu = models.ForeignKey(SPU,
                            related_name='skus',
                            on_delete=models.CASCADE,
                            verbose_name='SPU商品')
    # 这个SKU商品属于哪个第三级类别
    category = models.ForeignKey(GoodsCategory,
                                 on_delete=models.PROTECT,
                                 verbose_name='第三级类别')
    # 这个SKU商品的价格
    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                verbose_name='单价')
    # 这个SKU商品的进价
    cost_price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     verbose_name='进价')
    # 这个SKU商品的市场价
    market_price = models.DecimalField(max_digits=10,
                                       decimal_places=2,
                                       verbose_name='市场价')
    # 这个SKU商品的库存
    stock = models.IntegerField(default=0,
                                verbose_name='库存')
    # 这个SKU商品的销量
    sales = models.IntegerField(default=0,
                                verbose_name='销量')
    # 这个SKU商品的评价个数
    comments = models.IntegerField(default=0,
                                   verbose_name='评价数')
    # 这个SKU商品是否上架(是否在售)
    is_launched = models.BooleanField(default=True,
                                      verbose_name='是否上架销售')
    # 这个SKU商品对应的默认图片
    default_image = models.ImageField(max_length=200,
                                      default='',
                                      null=True,
                                      blank=True,
                                      verbose_name='默认图片')

    class Meta:
        db_table = 'tb_sku'
        verbose_name = '商品SKU'

    def __str__(self):
        return '%s: %s' % (self.id, self.name)


class SPUSpecification(BaseModel):
    """商品规格模型"""
    # 这个商品规格属于哪个SPU
    spu = models.ForeignKey(SPU,
                            related_name='specs',
                            on_delete=models.CASCADE,
                            verbose_name='商品')
    # 规格名称
    name = models.CharField(max_length=20,
                            verbose_name='规格名称')

    class Meta:
        db_table = 'tb_spu_specification'
        verbose_name = '商品规格'

    def __str__(self):
        return '%s: %s' % (self.spu.name, self.name)


class SpecificationOption(BaseModel):
    """规格选项模型"""
    # 这个选项属于哪个规格
    spec = models.ForeignKey(SPUSpecification,
                             related_name='options',
                             on_delete=models.CASCADE,
                             verbose_name='规格')
    # 规格选项的值
    value = models.CharField(max_length=20,
                             verbose_name='选项值')

    class Meta:
        db_table = 'tb_specification_option'
        verbose_name = '规格选项'

    def __str__(self):
        return '%s - %s' % (self.spec, self.value)


class SKUSpecification(BaseModel):
    """SKU具体规格模型"""
    # 对应的SKU值
    sku = models.ForeignKey(SKU,
                            related_name='specs',
                            on_delete=models.CASCADE,
                            verbose_name='SKU')
    # 对应哪一个规格
    spec = models.ForeignKey(SPUSpecification,
                             on_delete=models.PROTECT,
                             verbose_name='规格')
    # 对应哪一个选项
    option = models.ForeignKey(SpecificationOption,
                               on_delete=models.PROTECT,
                               verbose_name='选项')

    class Meta:
        db_table = 'tb_sku_specification'
        verbose_name = 'SKU规格'

    def __str__(self):
        return '%s: %s - %s' % (self.sku, self.spec.name, self.option.value)


class SKUImage(BaseModel):
    """SKU图片模型"""
    # 这个图片属于哪个SKU商品
    sku = models.ForeignKey(SKU,
                            on_delete=models.CASCADE,
                            verbose_name='sku')
    # 图片地址
    image = models.ImageField(verbose_name='图片地址')

    class Meta:
        db_table = 'tb_sku_image'
        verbose_name = 'SKU图片'

    def __str__(self):
        return '%s %s' % (self.sku.name, self.id)

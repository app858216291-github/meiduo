from django.db import models

from meiduo_mall.utils.base_model import BaseModel


class ContentCategory(BaseModel):
    """广告类别模型"""
    # 广告类别名称
    name = models.CharField(max_length=50,
                            verbose_name='名称')
    # 广告类别识别键名
    key = models.CharField(max_length=50,
                           verbose_name='类别键名')

    class Meta:
        db_table = 'tb_content_category'
        verbose_name = '广告类别'

    def __str__(self):
        return self.name


class Content(BaseModel):
    """广告内容模型"""
    # 一对多关联属性：关联广告类别
    category = models.ForeignKey(ContentCategory,
                                 on_delete=models.PROTECT,
                                 verbose_name='类别')
    # 广告标题
    title = models.CharField(max_length=100,
                             verbose_name='标题')
    # 广告被点击后跳转的 url
    url = models.CharField(max_length=300,
                           verbose_name='链接地址')

    # 广告展示图片地址
    image = models.ImageField(null=True,
                              blank=True,
                              verbose_name='图片')
    # 广告内容
    text = models.TextField(null=True,
                            blank=True,
                            verbose_name='内容')
    # 同类广告展示顺序
    sequence = models.IntegerField(verbose_name='排序')
    # 广告是否展示
    status = models.BooleanField(default=True,
                                 verbose_name='是否展示')

    class Meta:
        db_table = 'tb_content'
        verbose_name = '广告内容'

    def __str__(self):
        return self.category.name + ': ' + self.title

from haystack import indexes
from goods.models import SKU

class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    """SKU索引类"""
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """返回对应的模型类"""
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引结构数据的数据集"""
        return self.get_model().objects.filter(is_launched=True)
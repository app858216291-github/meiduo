


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
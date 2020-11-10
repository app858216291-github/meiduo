import base64
import pickle

from django_redis import get_redis_connection


class CartHelper:
    def __init__(self, request, response=None, alias='cart'):
        self.request = request
        self.user = request.user
        self.response = response

        if request.user.is_authenticated:
            # 如果用户已登录，创建 redis 链接
            self.cart_key = 'cart_%s' % request.user.id
            self.cart_selected_key = 'cart_selected_%s' % request.user.id
            self.redis_conn = get_redis_connection(alias)

    def _load_cookie_cart(self):
        """加载 cookie 中的购物车记录数据"""
        cookie_cart = self.request.COOKIES.get('carts')

        if cookie_cart:
            cart_dict = pickle.loads(base64.b64decode(cookie_cart))
        else:
            cart_dict = {}

        return cart_dict

    def _set_cookie_cart(self, cart_dict):
        """设置 cookie 中的购物车记录数据"""
        cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()
        self.response.set_cookie('carts', cookie_cart, 30 * 3600 * 24)

    def add_cart(self, sku_id, count, selected):
        """
        购物车记录添加：
        sku_id：添加记录的商品ID
        count：添加记录的商品数量
        selected：添加记录的勾选状态
        """
        if self.user.is_authenticated:
            # 用户已登录
            # 创建 redis 管道 pipeline
            pl = self.redis_conn.pipeline()

            # hincrby key field value：如果 field 在 hash 数据的字段中已存在，其值会进行累加，否则就是添加
            pl.hincrby(self.cart_key, sku_id, count)

            if selected:
                # 如果记录被勾选，将记录添加到 set 集合中
                # sadd key member...：向 set 集合数据中添加元素
                pl.sadd(self.cart_selected_key, sku_id)
            pl.execute()
        else:
            # 用户未登录
            cart_dict = self._load_cookie_cart()

            # 如果购物车中已添加该商品，数量需要先进行累加
            if sku_id in cart_dict:
                count += cart_dict[sku_id]['count']

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 重新将购物车记录设置到 cookie 中
            self._set_cookie_cart(cart_dict)

    def get_cart(self):
        """
        购物车记录获取
        """
        if self.user.is_authenticated:
            # 用户已登录
            # 获取用户添加到购物车中的商品 ID 和对应的数量 count
            # hgetall key：获取 hash 数据中所有的 field 和 value
            redis_cart = self.redis_conn.hgetall(self.cart_key)
            # 获取用户购物车中被勾选的商品 ID
            # smembers key：获取 set 集合数据中的所有元素
            selected_sku_ids = self.redis_conn.smembers(self.cart_selected_key)

            cart_dict = {}

            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_sku_ids
                }
        else:
            # 用户未登录
            # 从 cookie 数据中获取购物车数据
            cart_dict = self._load_cookie_cart()

        return cart_dict

    def update_cart(self, sku_id, count, selected):
        """
        购物车记录修改：
        sku_id：修改记录的商品 ID
        count：修改记录的商品数量
        selected：修改记录的勾选状态
        """
        if self.user.is_authenticated:
            # 用户已登录
            pl = self.redis_conn.pipeline()
            # 修改用户购物车中对应记录商品的数量
            # hset key field value：将 hash 数据中指定 field 字段的值设置为 value
            pl.hset(self.cart_key, sku_id, count)

            # 修改用户购物车中对应记录商品的勾选状态
            if selected:
                # sadd key member...：向 set 集合数据中添加元素
                pl.sadd(self.cart_selected_key, sku_id)
            else:
                # srem key member...：从 set 集合数据中移除元素
                pl.srem(self.cart_selected_key, sku_id)

            pl.execute()
        else:
            # 用户未登录
            cart_dict = self._load_cookie_cart()

            # 修改购物车记录中指定商品的数量和勾选状态
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 重新将购物车记录设置到 cookie 中
            self._set_cookie_cart(cart_dict)

    def remove_cart(self, sku_id):
        """
        购物车记录删除：
        sku_id：删除记录的商品 ID
        """
        if self.user.is_authenticated:
            # 用户已登录
            pl = self.redis_conn.pipeline()

            # 删除购物车记录对应的商品及其数量
            # hdel key field：删除 hash 数据中指定 field 字段及其值
            pl.hdel(self.cart_key, sku_id)

            # 删除购物车记录对应商品的勾选状态
            # srem key member...：从 set 集合数据中移除元素
            pl.srem(self.cart_selected_key, sku_id)
            pl.execute()
        else:
            cart_dict = self._load_cookie_cart()
            # 删除记录
            cart_dict.pop(sku_id, None)

            # 重新将购物车记录设置到 cookie 中
            self._set_cookie_cart(cart_dict)

    def select_cart(self, selected):
        """
        购物车记录全选和取消全选
        """
        if self.user.is_authenticated:
            sku_ids = self.redis_conn.hkeys(self.cart_key)

            cart_selected_key = 'cart_selected_%s' % self.user.id
            if selected:
                # 全选
                self.redis_conn.sadd(cart_selected_key, *sku_ids)
            else:
                # 取消全选
                self.redis_conn.srem(cart_selected_key, *sku_ids)
        else:
            cart_dict = self._load_cookie_cart()

            if cart_dict:
                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected
                self._set_cookie_cart(cart_dict)

    def get_redis_selected_cart(self):
        """
        获取redis中被勾选的记录
        """
        # sku_id count
        redis_conn = self.redis_conn
        redis_cart = redis_conn.hgetall(self.cart_key)
        redis_selected = redis_conn.smembers(self.cart_selected_key)

        cart_dict = {}
        for sku_id, count in redis_cart.items():
            if sku_id in redis_selected:
                cart_dict[int(sku_id)] = int(count)

        return cart_dict

    def clear_redis_selected_cart(self):
        """
        清除redis中被勾选的记录
        """
        redis_conn = self.redis_conn
        redis_cart = redis_conn.hgetall(self.cart_key)
        redis_selected = redis_conn.smembers(self.cart_selected_key)

        redis_conn.hdel(self.cart_key, *redis_selected)
        redis_conn.srem(self.cart_selected_key, *redis_selected)

    def merge_cookie_cart_to_redis(self):
        """将cookie中的购物车数据合并到redis"""
        # 加载 cookie 中的购物车数据
        cart_dict = self._load_cookie_cart()

        if not cart_dict:
            return None

        # 保存 cookie 购物车记录数据中对应的商品的id及添加的数量 count
        carts = {}
        # 保存cookie购物车记录数据中被勾选的记录对应的商品的id
        redis_cart_selected_add = []
        # 保存cookie购物车记录数据中未被勾选的记录对应的商品的id
        redis_cart_selected_remove = []

        # 遍历 cookie 中的购物车数据,分别存放到不同的位置
        for sku_id, values in cart_dict:
            count = values['count']
            selected = values['selected']

            carts[sku_id] = count
            if selected:
                redis_cart_selected_add.append(sku_id)
            else:
                redis_cart_selected_remove.append(sku_id)

        # 合并 cookie 中的购物车数据到 redis ,不存在则添加,存在则直接覆盖
        self.redis_conn.hmset(self.cart_key, carts)

        if redis_cart_selected_add:
            self.redis_conn.sadd(self.cart_selected_key, *redis_cart_selected_add)

        if redis_cart_selected_remove:
            self.redis_conn.srem(self.cart_selected_key,*redis_cart_selected_remove)

        # 清除 cookie 数据
        self.response.delete_cookie('carts')
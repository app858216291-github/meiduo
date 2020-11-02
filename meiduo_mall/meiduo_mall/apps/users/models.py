from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from meiduo_mall.utils.base_model import BaseModel

# Create your models here.
from django.conf import settings


class User(AbstractUser):
    """用户模型类"""
    # 增加mobile(手机号)字段
    mobile = models.CharField(max_length=11, unique=True,verbose_name='手机号')

    # 增加 email_active 字段
    #用来记录邮箱是否激活,默认为 False :未激活
    email_active = models.BooleanField(default=False,
                                       verbose_name='邮箱验证状态')

    # 新增默认地址关联属性,一个用户只能有一个默认收货地址
    default_address = models.OneToOneField('Address',
                                           related_name='owner',
                                           null=True,
                                           blank=True,
                                           on_delete=models.SET_NULL,
                                           verbose_name='默认地址')
    def generate_verify_email_url(self):
        """生成当前用户的邮箱验证链接"""
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 7200)

        # 用户信息加密,生成 token
        data = {'user_id': self.id,
                'email':self.email
                }
        token = serializer.dumps(data).decode()

        # 生成邮箱验证链接地址
        verify_url = settings.EMAIL_VERIFY_URL + token
        return verify_url

    @staticmethod
    def check_verify_email_token(token):
        """生成当前用户的邮箱验证链接"""
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)

        # 对加密的用户个人信息token进行解密
        try:
            data = serializer.loads(token)
        except BadData as e:
            return None
        else:
            user_id = data.get('user_id')
            email = data.get('email')

        # 获取对应用户对象数据
        try:
            user = User.objects.get(id=user_id,email=email)
        except User.DoesNotExist:
            return None
        else:
            return user


    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'


class Address(BaseModel):
    """用户地址模型类"""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')
    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,
                             related_name='city_addresses',
                             verbose_name='市')
    district = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='district_addresses',
                                 verbose_name='区')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='电话')
    phone = models.CharField(max_length=20,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='固定电话')
    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')
    is_delete = models.BooleanField(default=False, verbose_name='逻辑删除')
    class Meta:
        db_table = 'tb_addresses'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']

from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer, BadData

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
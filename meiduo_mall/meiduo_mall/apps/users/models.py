from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    """用户模型类"""
    # 增加mobile(手机号)字段
    moblie = models.CharField(max_length=11, unique=True,verbose_name='手机号')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
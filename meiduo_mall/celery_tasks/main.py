

from celery import Celery

# ①  创建Celery对象
celery_app = Celery('demo')

# ②  加载config.py的配置
celery_app.config_from_object('celery_tasks.config')

#celery worker 启动时自动加载任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])
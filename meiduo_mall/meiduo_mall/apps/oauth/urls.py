from django.urls import re_path
from oauth import views

urlpatterns = [
    re_path(r'^qq/authorization/$', views.QQLoginView.as_view()),
    re_path(r'^qq/oauth_callback/$', views.QQUserView.as_view()),
]
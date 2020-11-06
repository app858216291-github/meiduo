from django.urls import re_path
from goods import views

urlpatterns = [
    re_path(r'^list/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),
    re_path(r'^search/$', views.SKUSearchView.as_view()),
]
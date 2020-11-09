from django.urls import re_path
from carts import views

urlpatterns = [
    re_path(r'^carts/$', views.CartsView.as_view()),
    re_path(r'^carts/selection/$', views.ALLChoseView.as_view())
]


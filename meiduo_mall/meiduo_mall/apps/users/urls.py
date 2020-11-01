from django.urls import re_path
from users import views

urlpatterns = [
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$',
            views.UsernameCountView.as_view()),
    re_path(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',
            views.MobileCountView.as_view()),
    re_path(r'^register/$',
            views.RegisterView.as_view()),
    re_path(r'^csrf_token/$',
            views.CSRFTokenView.as_view()),
    re_path(r'^login/$',
            views.LoginView.as_view()),
    re_path(r'^logout/$',
            views.LogoutView.as_view()),
    re_path(r'^user/$',
            views.UserInfoView.as_view()),
    re_path(r'^user/email/$',
            views.UserEmailView.as_view()),
    re_path(r'^emails/verification/$',
            views.EmailVerifyView.as_view()),
]
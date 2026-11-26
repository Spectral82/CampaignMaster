from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify/<str:token>/", views.VerifyEmailView.as_view(), name="verify_email"),
    path("verify/", views.VerifyEmailNoticeView.as_view(), name="verify_notice"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("manager/users/", views.UserListView.as_view(), name="list"),
    path("manager/users/<int:pk>/block/", views.BlockUserView.as_view(), name="block"),
]

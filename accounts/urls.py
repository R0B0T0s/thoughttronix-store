from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.AccountView.as_view(), name="account"),
    path("email/", views.EmailChangeView.as_view(), name="email_change"),
    path(
        "password/",
        views.AccountPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-reset/",
        views.AccountPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        views.AccountPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.AccountPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        views.AccountPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("logout/", views.SignOutView.as_view(), name="logout"),
    path("addresses/", views.AddressListView.as_view(), name="address_list"),
    path("addresses/add/", views.AddressCreateView.as_view(), name="address_create"),
    path(
        "addresses/<int:pk>/edit/",
        views.AddressUpdateView.as_view(),
        name="address_update",
    ),
    path(
        "addresses/<int:pk>/delete/",
        views.AddressDeleteView.as_view(),
        name="address_delete",
    ),
    path(
        "addresses/<int:pk>/default-shipping/",
        views.SetDefaultShippingView.as_view(),
        name="address_default_shipping",
    ),
    path(
        "addresses/<int:pk>/default-billing/",
        views.SetDefaultBillingView.as_view(),
        name="address_default_billing",
    ),
]

from django.urls import path

from . import views

app_name = "coupons"

urlpatterns = [
    # Back office — staff-only, pk URLs per the URL conventions.
    path(
        "backoffice/coupons/",
        views.ManageCouponListView.as_view(),
        name="manage_coupons",
    ),
    path(
        "backoffice/coupons/add/",
        views.ManageCouponCreateView.as_view(),
        name="manage_coupon_create",
    ),
    path(
        "backoffice/coupons/<int:pk>/edit/",
        views.ManageCouponUpdateView.as_view(),
        name="manage_coupon_update",
    ),
    path(
        "backoffice/coupons/<int:pk>/toggle/",
        views.ToggleCouponActiveView.as_view(),
        name="manage_coupon_toggle",
    ),
]

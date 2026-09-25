"""Back-office coupon management: staff-only, per the URL conventions.

No delete — retiring (``is_active=False``) is the only removal action,
since a coupon already used on orders must keep existing for their
denormalized history to make sense.
"""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import StaffRequiredMixin

from .forms import CouponForm
from .models import Coupon


class ManageCouponListView(StaffRequiredMixin, ListView):
    template_name = "coupons/manage_coupons.html"
    context_object_name = "coupons"
    extra_context = {"section": "coupons"}

    def get_queryset(self):
        return Coupon.objects.prefetch_related("products")


class ManageCouponCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = "coupons/manage_coupon_form.html"
    success_url = reverse_lazy("coupons:manage_coupons")
    success_message = "“%(code)s” created."
    extra_context = {"section": "coupons"}


class ManageCouponUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = "coupons/manage_coupon_form.html"
    success_url = reverse_lazy("coupons:manage_coupons")
    success_message = "“%(code)s” saved."
    extra_context = {"section": "coupons"}


class ToggleCouponActiveView(StaffRequiredMixin, View):
    """POST-only: flip a coupon between active and retired."""

    def post(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.is_active = not coupon.is_active
        coupon.save(update_fields=["is_active"])
        state = "reactivated" if coupon.is_active else "retired"
        messages.success(request, f"“{coupon.code}” {state}.")
        return redirect("coupons:manage_coupons")

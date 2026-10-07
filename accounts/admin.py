from axes.admin import AccessAttemptAdmin
from axes.models import AccessAttempt
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Address, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        *DjangoUserAdmin.fieldsets,
        ("ThoughtTronix", {"fields": ("job_title",)}),
    )
    list_display = ("username", "email", "job_title", "is_staff")


admin.site.unregister(AccessAttempt)


@admin.register(AccessAttempt)
class StaffAccessAttemptAdmin(AccessAttemptAdmin):
    """django-axes' failed-login records, open to every employee.

    Roles are ``is_staff``, not permissions or Groups, so any staff member
    can view lockouts and delete one to let a customer sign in again.
    """

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "user",
        "city",
        "state",
        "is_default_shipping",
        "is_default_billing",
    )
    list_filter = ("is_default_shipping", "is_default_billing")
    search_fields = ("label", "recipient_name", "user__username")

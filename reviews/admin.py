from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """The store-wide safety net: find and remove abusive reviews."""

    list_display = (
        "user",
        "product",
        "rating",
        "created_at",
        "updated_at",
        "edited_by_staff",
    )
    list_filter = ("rating", "edited_by_staff")
    search_fields = ("user__username", "product__name", "comment")
    date_hierarchy = "created_at"
    list_select_related = ("user", "product")

"""Wishlist views — thin per the architecture convention.

The wishlist is always resolved from ``request.user``; no wishlist or
wishlist-item identifier ever appears in a URL.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import TemplateView

from products.models import Product

from .models import Wishlist


class WishlistView(LoginRequiredMixin, TemplateView):
    """The signed-in user's wishlist page."""

    template_name = "wishlist/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = Wishlist.for_user(self.request.user).listing()
        return context


class RemoveWishlistItemView(LoginRequiredMixin, View):
    """HTMX: remove a product from the wishlist page; the list swaps whole.

    The product is resolved through the signed-in user's own wishlist, so
    an entry on anyone else's wishlist can never be touched.
    """

    def post(self, request, pk):
        wishlist = Wishlist.for_user(request.user)
        wishlist.items.filter(product_id=pk).delete()
        return render(
            request,
            "wishlist/partials/_list.html",
            {"items": wishlist.listing()},
        )


class AddToWishlistView(LoginRequiredMixin, View):
    """HTMX: save a product; the button swaps to show the true saved state.

    Looks the product up in the full product set, not ``available()`` —
    unavailable products can be saved.
    """

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        wishlist = Wishlist.for_user(request.user)
        wishlist.add(product)
        return render(
            request,
            "wishlist/partials/_button.html",
            {"product": product, "on_wishlist": wishlist.contains(product)},
        )


class RemoveFromWishlistView(LoginRequiredMixin, View):
    """HTMX: unsave a product; the button swaps to show the true saved state.

    Like add, looks the product up in the full product set.
    """

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        wishlist = Wishlist.for_user(request.user)
        wishlist.remove(product)
        return render(
            request,
            "wishlist/partials/_button.html",
            {"product": product, "on_wishlist": wishlist.contains(product)},
        )

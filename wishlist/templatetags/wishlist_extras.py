from django import template

from wishlist.models import Wishlist

register = template.Library()


@register.simple_tag(takes_context=True)
def on_wishlist(context, product):
    """Whether the signed-in user has saved the product; False for visitors.

    Lets the product detail page show the wishlist button's state without
    the products app depending on the wishlist app.
    """
    user = context["user"]
    if not user.is_authenticated:
        return False
    return Wishlist.for_user(user).contains(product)

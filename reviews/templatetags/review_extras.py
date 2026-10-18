from django import template

from orders.models import OrderItem

register = template.Library()


@register.inclusion_tag("reviews/partials/_section.html", takes_context=True)
def reviews_section(context, product):
    """The product's whole Reviews section: summary, "Your review" box, list.

    Lets the product detail page show reviews without the products app
    depending on the reviews app.
    """
    user = context["user"]
    return {
        "product": product,
        "user": user,
        "summary": product.reviews.summary(),
        "reviews": product.reviews.select_related("user"),
        "purchased": user.is_authenticated
        and OrderItem.objects.purchased_by(user, product).exists(),
    }

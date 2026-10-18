from django import template

from reviews.views import section_context

register = template.Library()


@register.inclusion_tag("reviews/partials/_section.html", takes_context=True)
def reviews_section(context, product):
    """The product's whole Reviews section: summary, "Your review" box, list.

    Lets the product detail page show reviews without the products app
    depending on the reviews app.
    """
    return section_context(context["user"], product)

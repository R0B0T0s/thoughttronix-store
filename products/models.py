from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.templatetags.static import static
from django.urls import reverse

from .images import to_webp

# Categories with a dedicated placeholder illustration; anything else
# falls back to default.svg. A product without a usable uploaded image
# shows its category's placeholder.
DEFAULT_PLACEHOLDER = "images/placeholders/default.svg"
PLACEHOLDER_CATEGORIES = {
    "home-assistants",
    "neural-implants",
    "neural-wearables",
    "accessories",
    "defense",
    "legacy-products",
}


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:category", kwargs={"slug": self.slug})

    @property
    def placeholder_image(self):
        """Static path of the placeholder image shown for this category's products."""
        if self.slug in PLACEHOLDER_CATEGORIES:
            return f"images/placeholders/{self.slug}.svg"
        return DEFAULT_PLACEHOLDER


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(is_available=True)

    def search(self, text):
        """Simple icontains search over name and description."""
        return self.filter(
            models.Q(name__icontains=text) | models.Q(description__icontains=text)
        )


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    # Always a WebP written by replace_image; set it through that method.
    image = models.ImageField(upload_to="products/", blank=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})

    @property
    def has_image(self):
        """True when an image is set *and* its file is actually on disk."""
        return bool(self.image) and self.image.storage.exists(self.image.name)

    @property
    def placeholder_url(self):
        return static(self.category.placeholder_image)

    @property
    def display_image_url(self):
        """URL of the image to show: the upload if usable, else the placeholder."""
        return self.image.url if self.has_image else self.placeholder_url

    def replace_image(self, file):
        """Store ``file`` (already validated) as this product's image.

        The old file is deleted only after the new one is saved, so a
        failure part-way never leaves the product with no image at all.
        """
        old_name = self.image.name
        self.image.save(f"{self.slug}.webp", to_webp(file), save=True)
        if old_name and old_name != self.image.name:
            self.image.storage.delete(old_name)

    def remove_image(self):
        """Clear the image (back to the placeholder) and delete its file."""
        old_name = self.image.name
        if not old_name:
            return
        storage = self.image.storage
        self.image = ""
        self.save(update_fields=["image"])
        storage.delete(old_name)


@receiver(post_delete, sender=Product)
def delete_product_image_file(sender, instance, **kwargs):
    """A deleted product takes its image file with it — no orphans in media/."""
    if instance.image:
        instance.image.storage.delete(instance.image.name)

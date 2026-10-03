"""Product images: the upload rules, storage, display fallback, and back office."""

import io
from http import HTTPStatus

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from . import images
from .images import to_webp, validate_product_image
from .models import Product

pytestmark = pytest.mark.django_db


def make_upload(fmt="PNG", size=(800, 600), name=None, mode="RGB"):
    """An in-memory image upload, as a browser would send it."""
    buffer = io.BytesIO()
    Image.new(mode, size, color=(200, 40, 40) if mode == "RGB" else None).save(
        buffer, format=fmt
    )
    extension = {"JPEG": "jpg"}.get(fmt, fmt.lower())
    return SimpleUploadedFile(name or f"photo.{extension}", buffer.getvalue())


def rejection(upload):
    with pytest.raises(ValidationError) as excinfo:
        validate_product_image(upload)
    return " ".join(excinfo.value.messages)


# --- The rules ----------------------------------------------------------------


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_accepts_jpeg_png_and_webp(fmt):
    validate_product_image(make_upload(fmt))  # no exception


def test_rejects_other_formats_by_name():
    message = rejection(make_upload("GIF", mode="P"))

    assert "GIF" in message
    assert "JPG, PNG, or WebP" in message


def test_rejects_a_file_that_is_not_an_image():
    upload = SimpleUploadedFile("report.jpg", b"%PDF-1.7 definitely not a picture")

    assert "couldn't read this file as an image" in rejection(upload)


def test_rejects_a_truncated_image():
    whole = make_upload("PNG").read()
    upload = SimpleUploadedFile("cut.png", whole[: len(whole) // 2])

    assert "couldn't read this file as an image" in rejection(upload)


def test_rejects_files_over_the_size_limit(monkeypatch):
    monkeypatch.setattr(images, "MAX_UPLOAD_BYTES", 100)

    message = rejection(make_upload("PNG"))

    assert "MB" in message
    assert "limit is 10 MB" in message


def test_rejects_images_too_small_to_look_sharp():
    message = rejection(make_upload("PNG", size=(399, 900)))

    assert "399 × 900 pixels" in message
    assert "at least 400 pixels" in message


def test_rejects_absurd_pixel_dimensions(monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1000)

    assert "far too large" in rejection(make_upload("PNG"))


def test_to_webp_shrinks_to_display_size():
    result = Image.open(to_webp(make_upload("PNG", size=(3000, 2000))))

    assert result.format == "WEBP"
    assert result.size == (1200, 800)


def test_to_webp_keeps_transparency():
    buffer = io.BytesIO()
    Image.new("RGBA", (500, 500), (0, 0, 0, 0)).save(buffer, format="PNG")

    result = Image.open(to_webp(SimpleUploadedFile("logo.png", buffer.getvalue())))

    assert result.mode == "RGBA"


# --- Storage and display -------------------------------------------------------


def test_without_an_image_the_placeholder_shows(product):
    assert not product.has_image
    assert product.display_image_url.endswith("placeholders/home-assistants.svg")


def test_replace_image_stores_a_webp(product):
    product.replace_image(make_upload("JPEG"))

    product.refresh_from_db()
    assert product.has_image
    assert product.image.name.startswith("products/seraphine-home-hub")
    assert product.image.name.endswith(".webp")
    assert product.display_image_url == product.image.url


def test_replacing_deletes_the_old_file_only_after_saving(product):
    product.replace_image(make_upload("PNG"))
    old_name = product.image.name

    product.replace_image(make_upload("JPEG"))

    assert product.image.name != old_name
    assert product.image.storage.exists(product.image.name)
    assert not product.image.storage.exists(old_name)


def test_a_missing_file_falls_back_to_the_placeholder(product):
    product.replace_image(make_upload("PNG"))
    product.image.storage.delete(product.image.name)

    assert not product.has_image
    assert product.display_image_url == product.placeholder_url


def test_remove_image_clears_the_field_and_deletes_the_file(product):
    product.replace_image(make_upload("PNG"))
    name = product.image.name

    product.remove_image()

    product.refresh_from_db()
    assert not product.image
    assert not product.image.storage.exists(name)


def test_deleting_a_product_deletes_its_file(product):
    product.replace_image(make_upload("PNG"))
    storage, name = product.image.storage, product.image.name

    product.delete()

    assert not storage.exists(name)


def test_catalog_and_detail_show_the_uploaded_image(client, product):
    product.replace_image(make_upload("PNG"))

    for url in [reverse("products:catalog"), product.get_absolute_url()]:
        page = client.get(url).content.decode()
        assert product.image.url in page
        assert "onerror=" in page  # the browser-side fallback travels with it


def test_cart_shows_no_product_images(client, customer, cart_item):
    cart_item.product.replace_image(make_upload("PNG"))
    client.force_login(customer)

    page = client.get(reverse("orders:cart")).content.decode()

    assert cart_item.product.image.url not in page


# --- The back-office image panel -----------------------------------------------


def image_url(product):
    return reverse("products:manage_product_image", kwargs={"pk": product.pk})


def remove_url(product):
    return reverse("products:manage_product_image_remove", kwargs={"pk": product.pk})


def test_edit_page_shows_the_image_panel(client, staff_user, product):
    client.force_login(staff_user)

    page = client.get(
        reverse("products:manage_product_update", kwargs={"pk": product.pk})
    ).content.decode()

    assert "Product image" in page
    assert 'enctype="multipart/form-data"' in page
    assert "Upload image" in page


def test_staff_can_upload_an_image(client, staff_user, product):
    client.force_login(staff_user)

    response = client.post(
        image_url(product), {"image": make_upload("JPEG")}, follow=True
    )

    product.refresh_from_db()
    assert product.has_image
    assert "Image saved" in response.content.decode()


def test_a_rejected_upload_explains_why_and_saves_nothing(client, staff_user, product):
    client.force_login(staff_user)

    response = client.post(image_url(product), {"image": make_upload("GIF", mode="P")})

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "This file is a GIF image" in page
    assert "Product image" in page  # the edit page re-renders, panel and all
    product.refresh_from_db()
    assert not product.image
    assert not (product.image.storage.exists("products"))


def test_a_rejected_replacement_keeps_the_current_image(client, staff_user, product):
    product.replace_image(make_upload("PNG"))
    current = product.image.name
    client.force_login(staff_user)

    client.post(image_url(product), {"image": make_upload("PNG", size=(100, 100))})

    product.refresh_from_db()
    assert product.image.name == current
    assert product.has_image


def test_submitting_without_a_file_asks_for_one(client, staff_user, product):
    client.force_login(staff_user)

    page = client.post(image_url(product), {}).content.decode()

    assert "Choose an image file to upload." in page


def test_staff_can_remove_an_image(client, staff_user, product):
    product.replace_image(make_upload("PNG"))
    client.force_login(staff_user)

    client.post(remove_url(product))

    product.refresh_from_db()
    assert not product.image


def test_image_endpoints_are_staff_only(client, customer, product):
    for url in [image_url(product), remove_url(product)]:
        response = client.post(url, {"image": make_upload("PNG")})
        assert response.status_code == HTTPStatus.FOUND
        assert reverse("accounts:login") in response.url

    client.force_login(customer)
    for url in [image_url(product), remove_url(product)]:
        assert client.post(url).status_code == HTTPStatus.FORBIDDEN
    product.refresh_from_db()
    assert not product.image


def test_creating_a_product_lands_on_its_image_panel(client, staff_user, category):
    client.force_login(staff_user)

    response = client.post(
        reverse("products:manage_product_create"),
        {
            "name": "Pulse Halo",
            "slug": "pulse-halo",
            "price": "119.00",
            "category": str(category.pk),
        },
    )

    product = Product.objects.get(slug="pulse-halo")
    assert response.url == reverse(
        "products:manage_product_update", kwargs={"pk": product.pk}
    )

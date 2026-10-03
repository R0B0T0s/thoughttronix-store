"""Product image rules: what the store accepts, and how it stores it.

``validate_product_image`` decides whether a file is usable and, if not,
says why in plain English — it runs before anything is saved, so a
rejected file is never stored. ``to_webp`` shrinks an accepted image to
display size and re-encodes it as WebP. Back-office uploads and the seed
command both go through these two functions, so they follow one rule set.
"""

import io
import warnings

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MIN_SHORT_SIDE = 400
MAX_EDGE = 1200
WEBP_QUALITY = 85

# Pillow format name -> the name staff know it by.
ALLOWED_FORMATS = {"JPEG": "JPG", "PNG": "PNG", "WEBP": "WebP"}
ALLOWED_LIST = "JPG, PNG, or WebP"


def validate_product_image(file) -> None:
    """Raise ``ValidationError`` with a plain-English reason if ``file`` is unusable."""
    if file.size > MAX_UPLOAD_BYTES:
        megabytes = file.size / (1024 * 1024)
        raise ValidationError(
            f"This file is {megabytes:.1f} MB. The limit is 10 MB — try "
            "exporting a smaller version of the image.",
            code="too_large",
        )

    file.seek(0)
    try:
        with warnings.catch_warnings():
            # Pillow only *warns* for merely-huge images; treat that as a refusal.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(file) as image:
                image_format = image.format
                width, height = image.size
                if image_format in ALLOWED_FORMATS:
                    image.load()  # decode fully, so truncated files are caught
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError(
            "This image's dimensions are far too large to process safely. "
            "Please resize it to a normal photo size and try again.",
            code="too_many_pixels",
        ) from None
    except Exception:
        # Pillow reports unreadable or damaged files with many exception
        # types (OSError, ValueError, SyntaxError, ...); all mean the same.
        raise ValidationError(
            "We couldn't read this file as an image. It may be damaged, or it "
            "may not be a picture at all (for example, a PDF renamed to .jpg). "
            f"Please upload a {ALLOWED_LIST} image.",
            code="unreadable",
        ) from None
    finally:
        file.seek(0)

    if image_format not in ALLOWED_FORMATS:
        raise ValidationError(
            f"This file is a {image_format} image. The store accepts "
            f"{ALLOWED_LIST} images only — please convert it and try again.",
            code="wrong_format",
        )

    if min(width, height) < MIN_SHORT_SIDE:
        raise ValidationError(
            f"This image is only {width} × {height} pixels, so it would look "
            f"blurry on the product page. Please use an image at least "
            f"{MIN_SHORT_SIDE} pixels on its shortest side.",
            code="too_small",
        )


def to_webp(file) -> ContentFile:
    """Return ``file`` fitted within ``MAX_EDGE`` pixels and encoded as WebP.

    Expects a file that has already passed ``validate_product_image``.
    """
    file.seek(0)
    with Image.open(file) as original:
        image = ImageOps.exif_transpose(original)  # honor phone-camera rotation
        image.thumbnail((MAX_EDGE, MAX_EDGE))
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if image.has_transparency_data else "RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=WEBP_QUALITY)
    return ContentFile(buffer.getvalue())

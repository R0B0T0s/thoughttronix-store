from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from accounts.mixins import StaffRequiredMixin

from .forms import CategoryForm, ProductForm, ProductImageForm, TagForm
from .models import Category, Product, Tag


class CatalogView(ListView):
    """The public product catalog: search, tag and category filters, pagination.

    Filters arrive as querystring parameters (``q``, ``tag``, ``category``)
    and compose freely.
    """

    template_name = "products/catalog.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        products = Product.objects.select_related("category").prefetch_related("tags")
        query = self.request.GET.get("q", "").strip()
        if query:
            products = products.search(query)
        tag_slug = self.request.GET.get("tag", "")
        if tag_slug:
            products = products.filter(tags__slug=tag_slug)
        category_slug = self.request.GET.get("category", "")
        if category_slug:
            products = products.filter(category__slug=category_slug)
        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["active_tag"] = self.request.GET.get("tag", "")
        context["categories"] = Category.objects.all()
        context["tags"] = Tag.objects.all()
        return context


class CategoryView(CatalogView):
    """Browse a single category — the catalog scoped to one shelf."""

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ProductDetailView(DetailView):
    """A single product at its slug URL."""

    template_name = "products/detail.html"
    context_object_name = "product"
    queryset = Product.objects.select_related("category").prefetch_related("tags")


# --- The back office --------------------------------------------------------
#
# Staff-only catalog management. Every view gates on StaffRequiredMixin;
# URLs use pks per the URL conventions. The ``section`` context entry
# drives the active tab in the staff shell (backoffice/base.html).


class ManageProductListView(StaffRequiredMixin, ListView):
    """The back-office product list — every product, available or not."""

    template_name = "products/manage_products.html"
    context_object_name = "products"
    extra_context = {"section": "products"}

    def get_queryset(self):
        return Product.objects.select_related("category")


class ManageProductCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    """New products land on their edit page, where the image panel lives."""

    model = Product
    form_class = ProductForm
    template_name = "products/manage_product_form.html"
    success_message = "“%(name)s” created. You can add its image below."
    extra_context = {"section": "products"}

    def get_success_url(self):
        return reverse("products:manage_product_update", kwargs={"pk": self.object.pk})


class ManageProductUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/manage_product_form.html"
    success_url = reverse_lazy("products:manage_products")
    success_message = "“%(name)s” saved."
    extra_context = {"section": "products"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_form"] = ProductImageForm()
        return context


class ManageProductImageView(StaffRequiredMixin, SingleObjectMixin, FormView):
    """The image panel's upload (POST only).

    A rejected file re-renders the edit page with the reason under the
    file chooser; nothing is saved. An accepted file replaces the old one.
    """

    model = Product
    form_class = ProductImageForm
    template_name = "products/manage_product_form.html"
    http_method_names = ["post"]
    extra_context = {"section": "products"}

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object.replace_image(form.cleaned_data["image"])
        messages.success(self.request, f"Image saved for “{self.object.name}”.")
        return redirect("products:manage_product_update", pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_form"] = context.pop("form")
        context["form"] = ProductForm(instance=self.object)
        return context


class ManageProductImageRemoveView(StaffRequiredMixin, SingleObjectMixin, View):
    """The image panel's Remove button: back to the category placeholder."""

    model = Product
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        product.remove_image()
        messages.success(
            request, f"Image removed. “{product.name}” now shows its placeholder."
        )
        return redirect("products:manage_product_update", pk=product.pk)


class ManageProductDeleteView(StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    context_object_name = "product"
    template_name = "products/manage_product_confirm_delete.html"
    success_url = reverse_lazy("products:manage_products")
    success_message = "Product deleted."
    extra_context = {"section": "products"}


class ManageCatalogView(StaffRequiredMixin, TemplateView):
    """Categories and tags on one management page."""

    template_name = "products/manage_catalog.html"
    extra_context = {"section": "catalog"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.annotate(
            product_count=Count("products")
        )
        context["tags"] = Tag.objects.annotate(product_count=Count("products"))
        return context


class ManageCategoryCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” created."
    extra_context = {"section": "catalog", "kind": "category"}


class ManageCategoryUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” saved."
    extra_context = {"section": "catalog", "kind": "category"}


class ManageTagCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” created."
    extra_context = {"section": "catalog", "kind": "tag"}


class ManageTagUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” saved."
    extra_context = {"section": "catalog", "kind": "tag"}

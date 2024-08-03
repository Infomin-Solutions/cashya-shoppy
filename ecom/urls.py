from . import views
from django.urls import path

urlpatterns = [
    path(
        'category-products', views.category_products_view, name='category-products'),
    path('products', views.products_view, name='products'),
    path('product-detail', views.product_detail, name='product-detail'),
]

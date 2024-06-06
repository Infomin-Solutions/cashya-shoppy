from . import views
from django.urls import path

urlpatterns = [
    path('base', views.base_view, name='base'),
    path(
        'category-products', views.category_products_view, name='category-products'),
    path('product-card', views.product_card_view, name='product-card'),
    path('products', views.products_view, name='products'),
    path('product-detail', views.product_detail, name='product-detail')
]

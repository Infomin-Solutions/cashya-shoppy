import json
from . import models
from . import views_api as views
from django.shortcuts import render

# Create your views here.


def base_view(request):
    return render(
        request,
        'ecom/base.html',
        context={}
    )


def category_products_view(request):
    viewset = views.CategoryProductViewSet()
    viewset.request = request
    res = viewset.list(request).data
    data = json.loads(json.dumps(res))
    return render(
        request,
        'ecom/category-products.html',
        context={
            'data': data
        }
    )


def product_card_view(request):
    return render(
        request,
        'ecom/product-card.html',
        context={}
    )


def products_view(request):
    return render(
        request,
        'ecom/products.html',
        context={}
    )

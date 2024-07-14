import json
from . import models
from .api.views import CategoryProductViewSet, ProductViewSet
from django.shortcuts import render

# Create your views here.


def category_products_view(request):
    viewset = CategoryProductViewSet()
    viewset.request = request
    res = viewset.list(request).data
    data = json.loads(json.dumps(res))
    return render(
        request,
        'ecom/category-products.dhtml',
        context={
            'data': data
        }
    )


def products_view(request):
    return render(
        request,
        'ecom/products.html',
        context={}
    )


def product_detail(request):
    viewset = ProductViewSet()
    viewset.request = request
    request.query_params = {}
    viewset.kwargs = {'pk': 1}
    res = viewset.retrieve(request).data
    data = json.loads(json.dumps(res))
    return render(
        request,
        'ecom/product-detail.dhtml',
        context={
            'data': data
        }
    )

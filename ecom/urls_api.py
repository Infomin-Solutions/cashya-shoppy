from . import views_api as views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'products', views.ProductViewSet, basename='products')
router.register(
    r'category-products', views.CategoryProductViewSet, basename='category-products')
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')


urlpatterns = router.urls

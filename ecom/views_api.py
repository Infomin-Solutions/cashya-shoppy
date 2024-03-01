from . import models
from . import serializers

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import SessionAuthentication
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet, generics

from rest_framework_simplejwt.authentication import JWTAuthentication


# Create your views here.


class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class ProductViewSet(ReadOnlyModelViewSet):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer
    permission_classes = (AllowAny, )
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, )
    search_fields = '__all__'
    ordering_fields = '__all__'


class CartViewSet(ViewSet):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    serializer_class = serializers.CartItemSerializer

    def list(self, request):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        serializer = serializers.CartSerializer(cart)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(
            models.CartItem, cart=cart, product_variant_id=pk)
        serializer = serializers.CartItemSerializer(cart_item)
        return Response(serializer.data)

    def create(self, request):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        serializer = serializers.CartItemSerializer(
            data=request.data, context={'create': True, 'cart': cart})
        if serializer.is_valid():
            serializer.save()
            response = self.list(request)
            response.status_code = status.HTTP_201_CREATED
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(
            models.CartItem, cart=cart, product_variant_id=pk)
        serializer = serializers.CartItemSerializer(
            cart_item, data=request.data, context={'cart': cart})
        if serializer.is_valid():
            serializer.save()
            response = self.list(request)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(
            models.CartItem, cart=cart, product_variant_id=pk)
        serializer = serializers.CartItemSerializer(
            cart_item, data=request.data, partial=True, context={'cart': cart})
        if serializer.is_valid():
            serializer.save()
            response = self.list(request)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(
            models.CartItem, cart=cart, product_variant_id=pk)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    pagination_class = PageNumberPagination
    serializer_class = serializers.OrderSerializer

    def get_queryset(self):
        return models.Order.objects.filter(user=self.request.user)

    def create(self, request):
        serializer = serializers.OrderSerializer(
            data=request.data, context={'user': request.user})
        if serializer.is_valid():
            cart, _ = models.Cart.objects.get_or_create(user=request.user)
            cart_items = models.CartItem.objects.filter(cart=cart)
            serializer.save()
            total = 0
            for item in cart_items:
                total += item.product_variant.price * item.quantity
                order_item = models.OrderItem(
                    product_name=item.product_variant.product.name,
                    variant_name=item.product_variant.name,
                    product_variant=item.product_variant,
                    order_id=serializer.instance.id,
                    quantity=item.quantity,
                    price=item.product_variant.price,
                    total=item.product_variant.price * item.quantity
                )
                order_item.save()
            serializer.instance.total = total
            serializer.instance.save()
            cart.product_variants.clear()
            models.OrderStatus.objects.create(
                order=serializer.instance, status=0)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

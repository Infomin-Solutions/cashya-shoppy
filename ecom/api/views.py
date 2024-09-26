from ecom import utils
from ecom import models
from . import serializers

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import SessionAuthentication
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet, generics, ModelViewSet

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
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ['name', 'description']
    ordering_fields = '__all__'
    format_kwarg = None  # to access from other views


class CategoryProductViewSet(ReadOnlyModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategoryProductSerializer
    permission_classes = (AllowAny, )
    pagination_class = None
    format_kwarg = None  # to access from other views


class WhishlistViewSet(ViewSet, generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (JWTAuthentication, SessionAuthentication)

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.WishlistSerializer
        return serializers.WishlistCreateSerializer

    def get_queryset(self):
        return models.Wishlist.objects.filter(user=self.request.user)

    def retrieve(self, request, pk):
        wishlist = get_object_or_404(
            models.Wishlist, product_id=pk, user=request.user)
        serializer = serializers.WishlistSerializer(
            wishlist, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        serializer = serializers.WishlistCreateSerializer(
            data=request.data, context={'user': request.user})
        if serializer.is_valid():
            product_id = serializer.validated_data['product'].id
            product = models.Product.objects.filter(id=product_id)
            if product.exists():
                wishlist, created = models.Wishlist.objects.get_or_create(
                    user=request.user, product=product[0])
                if created:
                    return Response(serializers.WishlistSerializer(
                        wishlist,
                        context={'request': request}
                    ).data, status=status.HTTP_201_CREATED)
                return Response({'detail': 'Product already in wishlist'}, status=status.HTTP_200_OK)
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        wishlist = get_object_or_404(
            models.Wishlist, product_id=pk, user=request.user)
        wishlist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartViewSet(ViewSet):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    serializer_class = serializers.CartItemSerializer

    def list(self, request):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        serializer = serializers.CartSerializer(
            cart, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(
            models.CartItem, cart=cart, product_variant_id=pk)
        serializer = serializers.CartItemSerializer(
            cart_item, context={'request': request})
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
        'Create Order and return payment config'
        serializer = serializers.OrderSerializer(
            data=request.data, context={'user': request.user})
        if serializer.is_valid():
            cart, _ = models.Cart.objects.get_or_create(user=request.user)
            serializer.instance.name = cart.address.name
            serializer.instance.address = cart.address.address
            serializer.instance.city = cart.address.city
            serializer.instance.state = cart.address.state
            serializer.instance.pincode = cart.address.pincode
            serializer.instance.landmark = cart.address.landmark
            serializer.instance.phone_number = cart.address.phone_number
            serializer.instance.alternate_phone_number = cart.address.alternate_phone_number
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

    def update(self, request, pk):
        'Return the payment config for the order'
        pass


class CouponViewSet(ViewSet):
    queryset = models.Coupon.objects.all()
    serializer_class = serializers.CouponSerializer
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    pagination_class = None

    def retrieve(self, request, pk=None):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        serializer = serializers.CouponSerializer(
            data={'code': cart.coupon.code if cart.coupon else None}, context={'cart': cart})
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        serializer = serializers.CouponSerializer(
            data=request.data, context={'cart': cart})
        if serializer.is_valid():
            cart.coupon = models.Coupon.objects.get(
                code=serializer.validated_data['code'])
            cart.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        cart, _ = models.Cart.objects.get_or_create(user=request.user)
        cart.coupon = None
        cart.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressViewSet(ModelViewSet):
    serializer_class = serializers.AddressSerializer
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    pagination_class = None

    def get_queryset(self):
        return models.Address.objects.filter(user=self.request.user)

    def set_default(self, serializer):
        cart, _ = models.Cart.objects.get_or_create(user=self.request.user)
        if serializer.instance.selected:
            cart.address = serializer.instance
            cart.save()
        else:
            addresses = models.Address.objects.filter(
                user=self.request.user, selected=True)
            if not addresses.exists():
                cart.address = None
                cart.save()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        self.set_default(serializer)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self.set_default(serializer)

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cart, _ = models.Cart.objects.get_or_create(user=self.request.user)
        if cart.address == instance:
            cart.address = None
            cart.save()


class PaymentViewSet(ViewSet):
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    pagination_class = None
    serializer_class = serializers.PaymentSerializer

    def list(self, request):
        'This method should return the list of payment methods available with meta data'
        cart = models.Cart.objects.get(user=request.user)
        methods = []
        for mode in utils.PAYMENT_MODES:
            methods.append({
                'name': mode[1],
                'value': mode[0],
                'selected': cart.payment_mode == mode[0]
            })
        return Response({
            'methods': methods
        })

    def retrieve(self, request, pk):
        'Retrive the payment details for the order'
        pass

    def create(self, request):
        'Create a payment for the order'
        cart = models.Cart.objects.get(user=request.user)
        serializer = serializers.PaymentSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            cart.payment_mode = serializer.validated_data['payment_method']
            cart.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

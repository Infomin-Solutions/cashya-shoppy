from random import random
from ecom import utils
from ecom import models
from django.db.models import Min, Max
from rest_framework import serializers
from rest_framework.serializers import ValidationError
import re


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    total_products = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Category
        fields = ['id', 'name', 'image', 'image_url', 'total_products']
        read_only_fields = ['id', 'image_url', 'total_products']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and obj.image.image:
            return request.build_absolute_uri(obj.image.image.url)
        return None

    def get_total_products(self, obj):
        return obj.products.count()


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductVariant
        fields = [
            'id', 'name', 'mrp', 'price', 'available']
        read_only_fields = ['id']


class ProductImageSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.ProductImage
        fields = ['id', 'name', 'image_url']
        read_only_fields = ['id', 'image_url']

    def get_name(self, obj):
        return obj.image.name

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and obj.image.image:
            return request.build_absolute_uri(obj.image.image.url)
        return None


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(
        many=True, read_only=True, source='productimage_set')
    variants = ProductVariantSerializer(
        many=True, read_only=True)
    start_price = serializers.SerializerMethodField(read_only=True)
    end_price = serializers.SerializerMethodField(read_only=True)
    whishlist = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Product
        fields = [
            'id', 'name', 'description', 'category', 'available', 'whishlist', 'variants', 'images', 'start_price', 'end_price']
        read_only_fields = ['id', 'variants', 'images', 'whishlist']

    def get_start_price(self, obj):
        return obj.variants.aggregate(Min('price'))['price__min']

    def get_end_price(self, obj):
        if obj.variants.count() > 1:
            return obj.variants.aggregate(Max('price'))['price__max']
        return None

    def get_whishlist(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return models.Wishlist.objects.filter(
                user=request.user, product=obj).exists()
        return False


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = models.Wishlist
        fields = ['product', 'added_at']


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Wishlist
        fields = ['product']


class CategoryProductSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    total_products = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Category
        fields = ['id', 'name', 'products', 'total_products']

    def get_total_products(self, obj):
        return obj.products.count()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Address
        fields = [
            'id', 'name', 'address', 'city', 'state', 'pincode', 'landmark',
            'phone_number', 'alternate_phone_number', 'nickname', 'selected', 'company_name', 'gstin']

    def validate_company_name(self, value):
        if self.initial_data.get('gstin') and not value:
            raise ValidationError('Company name is required')
        return value

    def validate_gstin(self, value):
        if self.initial_data.get('company_name', None) and not value:
            raise ValidationError('GSTIN is required')
        if value:
            value = value.upper()
            regex = re.compile(
                r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
            if not regex.match(value):
                raise ValidationError('Invalid GSTIN')
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.CartItem
        fields = [
            'product_variant', 'product', 'quantity', 'image']
        read_only_fields = ['id', 'product']
        lookup_field = 'product_variant'

    def get_product(self, obj: models.CartItem):
        return {
            'product_id': obj.product_variant.product.id,
            'product_name': obj.product_variant.product.name,
            'variant_id': obj.product_variant.id,
            'variant_name': obj.product_variant.name,
            'price': obj.product_variant.price,
            'mrp': obj.product_variant.mrp,
        }

    def get_image(self, obj: models.CartItem):
        request = self.context.get('request')
        images = obj.product_variant.product.images.all()
        if images.exists():
            image = images[0]
            name = image.name
            image_url = request.build_absolute_uri(image.image.url)
            return {
                'name': name,
                'image_url': image_url
            }
        return None

    def validate_product_variant(self, value):
        cart_items = models.CartItem.objects.filter(
            cart_id=self.context['cart'], product_variant=value)
        if self.context.get('create') and cart_items.exists():
            cart_items.delete()
        return value

    def create(self, validated_data):
        validated_data['cart'] = self.context['cart']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['cart'] = self.context['cart']
        return super().update(instance, validated_data)


class CalculateItem:
    """A simple class to hold calculate item data"""

    def __init__(self, name, value, info=None):
        self.name = name
        self.value = value
        self.info = info


class CalculateItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.DecimalField(max_digits=10, decimal_places=2)
    info = serializers.CharField(required=False, allow_null=True, default=None)


class CalculateSerializer(serializers.Serializer):
    calculate = CalculateItemSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        calculate_items = []

        # Sub total
        sub_total = instance.sub_total
        sub_total_info = random.choice(
            [None, 'This is the total of products without any discounts applied'])
        calculate_items.append(CalculateItem(
            name='sub total',
            value=sub_total,
            info=sub_total_info
        ))

        # Discount
        discount = utils.calculate_discount(instance)
        if discount > 0:
            discount_info = random.choice([None, 'Discount applied'])
            if instance.coupon:
                discount_info = f'Discount applied with coupon: {instance.coupon.code}'
            calculate_items.append(CalculateItem(
                name='discount',
                value=discount,
                info=discount_info
            ))

        # Shipping
        shipping = utils.calculate_shipping(instance)
        if shipping == 0:
            shipping_info = random.choice([None, 'Free shipping applied'])
        else:
            shipping_info = random.choice([None, 'Shipping charges applied'])
        calculate_items.append(CalculateItem(
            name='shipping',
            value=shipping,
            info=shipping_info
        ))

        # Tax
        tax = utils.calculate_tax(instance)
        tax_info = random.choice([None, 'Tax applied at 18%'])
        calculate_items.append(CalculateItem(
            name='tax',
            value=tax,
            info=tax_info
        ))

        # Total
        total = utils.calculate_total(instance)
        total_info = random.choice([None, 'Total amount to be paid'])
        calculate_items.append(CalculateItem(
            name='total',
            value=total,
            info=total_info
        ))

        # Serialize the CalculateItem objects using CalculateItemSerializer
        serializer = CalculateItemSerializer(calculate_items, many=True)
        return {
            'calculate': serializer.data
        }


class CartSerializer(serializers.ModelSerializer):
    products = CartItemSerializer(
        many=True, read_only=True, source='cartitem_set')
    coupon = serializers.SerializerMethodField(read_only=True)
    calculate = serializers.SerializerMethodField(read_only=True)
    sub_total = serializers.SerializerMethodField(read_only=True)
    total = serializers.SerializerMethodField(read_only=True)
    address = AddressSerializer(read_only=True)

    class Meta:
        model = models.Cart
        fields = [
            'user', 'address', 'products', 'coupon', 'payment_mode', 'calculate', 'sub_total', 'total'
        ]
        read_only_fields = [
            'user', 'address', 'products', 'coupon', 'payment_mode', 'calculate', 'sub_total', 'total'
        ]

    def get_coupon(self, obj):
        if obj.coupon:
            return obj.coupon.code
        return None

    def get_calculate(self, obj):
        calculate_serializer = CalculateSerializer()
        return calculate_serializer.to_representation(obj)['calculate']

    def get_sub_total(self, obj):
        return obj.sub_total

    def get_total(self, obj):
        return utils.calculate_total(obj)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderItem
        fields = [
            'product_name', 'variant_name', 'product_variant', 'quantity', 'price', 'total']
        read_only_fields = [
            'product_name', 'variant_name', 'product_variant', 'quantity', 'price', 'total']


class OrderStatusSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.OrderStatus
        fields = ['name', 'status', 'created_at']
        read_only_fields = ['name', 'created_at']

    def get_name(self, obj):
        return models.STATUS_CHOICES[obj.status]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    statuses = OrderStatusSerializer(many=True, read_only=True)

    class Meta:
        model = models.Order
        fields = [
            'id', 'name', 'address', 'city', 'state', 'pincode', 'landmark', 'payment_mode',
            'phone_number', 'alternate_phone_number', 'total', 'created_at', 'status', 'items', 'statuses']
        read_only_fields = [
            'id', 'name', 'address', 'city', 'state', 'pincode', 'landmark', 'payment_mode',
            'phone_number', 'alternate_phone_number', 'total', 'created_at', 'status', 'items', 'statuses']

    def validate(self, attrs):
        if not models.CartItem.objects.filter(cart__user=self.context['user']).count():
            raise ValidationError('Your cart is empty')
        if not models.Cart.objects.filter(user=self.context['user']).first().address:
            raise ValidationError('Address is required for placing order')
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data['user'] = self.context['user']
        return super().create(validated_data)


class CouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100, required=True)

    def validate_code(self, code: str):
        code = code.upper()
        cart = self.context.get('cart')
        if not cart:
            raise ValidationError('Cart is required for coupon validation')
        coupon = models.Coupon.objects.filter(code=code).first()
        if not coupon:
            raise ValidationError('Invalid coupon code')
        return utils.validate_coupon(cart, coupon)


class PaymentSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=[], required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context.get('request').user
        if user and user.is_authenticated:
            self.fields['payment_method'].choices = self.get_user_specific_choices(
                user)

    def get_user_specific_choices(self, user):
        return [(None, '-')] + utils.PAYMENT_MODES

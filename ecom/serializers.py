# serializers.py
from rest_framework import serializers
from . import models
from rest_framework.serializers import ValidationError
from django.db.models import Min, Max


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

    class Meta:
        model = models.Product
        fields = [
            'id', 'name', 'description', 'category', 'available', 'variants', 'images', 'start_price', 'end_price']
        read_only_fields = ['id', 'variants', 'images']

    def get_start_price(self, obj):
        return obj.variants.aggregate(Min('price'))['price__min']

    def get_end_price(self, obj):
        if obj.variants.count() > 1:
            return obj.variants.aggregate(Max('price'))['price__max']
        return None


class CategoryProductSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    total_products = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Category
        fields = ['id', 'name', 'products', 'total_products']

    def get_total_products(self, obj):
        return obj.products.count()


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
        if obj.product_variant.product.images.first():
            image = obj.product_variant.product.images.first()
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


class CartSerializer(serializers.ModelSerializer):
    products = CartItemSerializer(
        many=True, read_only=True, source='cartitem_set')

    class Meta:
        model = models.Cart
        fields = ['user', 'products']
        read_only_fields = ['user', 'products']


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
        fields = ['id', 'total', 'created_at', 'status', 'items', 'statuses']
        read_only_fields = [
            'id', 'total', 'created_at', 'status', 'items', 'statuses']

    def validate(self, attrs):
        if not models.CartItem.objects.filter(cart__user=self.context['user']).count():
            raise ValidationError('Your cart is empty')
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data['user'] = self.context['user']
        return super().create(validated_data)

from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    image = models.ForeignKey(
        Image, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='categories')

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products')
    images = models.ManyToManyField(
        Image, through='ProductImage', related_name='products')
    available = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductImage(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.DO_NOTHING)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='cart')
    product_variants = models.ManyToManyField(
        ProductVariant, through='CartItem', related_name='carts')

    def __str__(self):
        return f"{self.id} {self.user.username}'s cart"


class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


STATUS_CHOICES = [
    'Pending',
    'Paid',
    'Processing',
    'Billed',
    'Cancelled',
    'Despatched',
    'Delivered',
    'Returned'
]


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id}"

    def get_status_choices(self, current_status=None):
        if current_status is None:
            current_status = self.statuses.all().order_by('status').last().status
        statuses = [(index, choice)
                    for index, choice in enumerate(STATUS_CHOICES)]
        return statuses[current_status:]


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100)
    variant_name = models.CharField(max_length=100)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.DO_NOTHING, related_name='order_items')
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)


class OrderStatus(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.IntegerField(
        choices=[(index, choice) for index, choice in enumerate(STATUS_CHOICES)])
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='statuses')

    class Meta:
        ordering = ['status']
        verbose_name_plural = 'order statuses'

    def __str__(self):
        return STATUS_CHOICES[self.status]

from django.db import models
from django.db.models import F, Sum
from authentication.models import User
from phonenumber_field.modelfields import PhoneNumberField

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
        Image, blank=True, null=True, on_delete=models.SET_NULL, related_name='categories')

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
        ordering = ['-available', 'name']

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    mrp = models.FloatField()
    price = models.FloatField()
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-available', 'sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductImage(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.DO_NOTHING)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class Coupon(models.Model):
    code = models.CharField(max_length=100, unique=True)
    discount = models.FloatField()
    coupon_type = models.CharField(choices=(
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed')
    ), max_length=10)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(
        help_text='Leave Empty if always active', blank=True, null=True)
    valid_to = models.DateTimeField(
        help_text='Leave Empty if always active', blank=True, null=True)
    minimum_order_value = models.FloatField(
        help_text='Leave Empty to use default', blank=True, null=True)
    quantity = models.PositiveIntegerField(
        help_text='Leave Empty if unlimited', blank=True, null=True, default=1)

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code


class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='cart')
    address = models.OneToOneField(
        'Address', on_delete=models.SET_NULL, blank=True, null=True, related_name='cart'
    )
    product_variants = models.ManyToManyField(
        ProductVariant, through='CartItem', related_name='carts')
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, blank=True, null=True)
    payment_mode = models.CharField(
        max_length=20, blank=True, null=True)

    @property
    def sub_total(self):
        total = self.product_variants.through.objects.filter(cart=self).aggregate(
            total=Sum(F('product_variant__price') * F('quantity'))
        )['total'] or 0
        return round(total, 2)

    def __str__(self):
        return f"{self.id} {self.user.username}'s cart"


class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Wishlist(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='whishlists')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='whishlists')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s whishlist"


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
    name = models.CharField(max_length=100)
    address = models.TextField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    landmark = models.CharField(max_length=100, blank=True, null=True)
    phone_number = PhoneNumberField(blank=False, null=False)
    alternate_phone_number = PhoneNumberField(blank=True, null=True)
    total = models.FloatField(default=0)
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
    quantity = models.PositiveIntegerField(blank=True, null=True)
    price = models.FloatField()
    total = models.FloatField()


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


class Address(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100)
    address = models.TextField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    landmark = models.CharField(max_length=100, blank=True, null=True)
    phone_number = PhoneNumberField(blank=False, null=False)
    alternate_phone_number = PhoneNumberField(blank=True, null=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    selected = models.BooleanField(default=False)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        ordering = ['-selected']

    def __str__(self):
        return f"{self.user.username}'s address"

    def save(self, *args, **kwargs):
        if self.selected:
            self.user.addresses.filter(selected=True).update(selected=False)
        super().save(*args, **kwargs)

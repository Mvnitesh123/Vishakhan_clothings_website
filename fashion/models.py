# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from cloudinary.models import CloudinaryField
from django.contrib.postgres.fields import ArrayField
from .fields import EncryptedCharField, EncryptedTextField



# =========================================================
# USER MODEL
# =========================================================

class User(AbstractUser):
    email = models.EmailField(unique=True)

    first_name = EncryptedCharField(blank=True)
    last_name = EncryptedCharField(blank=True)
    phone = EncryptedCharField(blank=True)

    profile_image = CloudinaryField(
        'image',
        folder='users/profile/',
        blank=True,
        null=True
    )


    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            # Get prefix before @ from email
            email_prefix = self.email.split('@')[0]
            self.username = email_prefix
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


# =========================================================
# CATEGORY MODEL
# =========================================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    slug = models.SlugField(unique=True, blank=True)

    image = CloudinaryField(
        'image',
        folder='categories/',
        blank=True,
        null=True
    )


    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# =========================================================
# SUB CATEGORY MODEL
# =========================================================

class SubCategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )

    name = models.CharField(max_length=100)

    slug = models.SlugField(blank=True)

    image = CloudinaryField(
        'image',
        folder='subcategories/',
        blank=True,
        null=True
    )


    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['category', 'name']
        verbose_name_plural = "Sub Categories"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.name}"




# =========================================================
# PRODUCT MODEL
# =========================================================

class Product(models.Model):

    STOCK_STATUS = (
        ('IN_STOCK', 'In Stock'),
        ('OUT_OF_STOCK', 'Out Of Stock'),
        ('LIMITED', 'Limited'),
    )

    PRODUCT_TYPE = (
        ('Shirt', 'Shirt'),
        ('Pant', 'Pant'),
        ('Shorts & Track', 'Shorts & Track'),
        ('T-shirt', 'T-shirt'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True
    )

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True
    )

    product_type = models.CharField(
        max_length=50,
        choices=PRODUCT_TYPE,
        default='Shirt'
    )


    is_trending = models.BooleanField(default=False, db_index=True)

    name = models.CharField(max_length=255)

    slug = models.SlugField(unique=True, blank=True)

    image = CloudinaryField(
        'image',
        folder='products/',
        blank=True,
        null=True
    )

    short_description = models.CharField(max_length=300)

    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)

    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    sku = models.CharField(max_length=100, unique=True)

    is_featured = models.BooleanField(default=False, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    views = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.discount_price is not None and self.discount_price >= self.price:
            raise ValidationError({
                'discount_price': "Discount price must be less than the original price."
            })

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.full_clean()
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def stock(self):
        if hasattr(self, '_prefetched_objects_cache') and 'variants' in self._prefetched_objects_cache:
            return sum(variant.stock for variant in self._prefetched_objects_cache['variants'] if variant.is_active)
        return sum(variant.stock for variant in self.variants.filter(is_active=True))

    @property
    def stock_status(self):
        total_stock = self.stock
        if total_stock <= 0:
            return 'OUT_OF_STOCK'
        elif total_stock < 5:
            return 'LIMITED'
        else:
            return 'IN_STOCK'

    @property
    def get_stock_status_display(self):
        status = self.stock_status
        if status == 'OUT_OF_STOCK':
            return 'Out Of Stock'
        elif status == 'LIMITED':
            return 'Limited'
        else:
            return 'In Stock'

    @property
    def discount_percentage(self):
        if self.price and self.discount_price:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return int(discount)
        return 0

    @property
    def avg_rating(self):
        if hasattr(self, '_avg_rating'):
            return self._avg_rating
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return float(result) if result is not None else 0.0

    @avg_rating.setter
    def avg_rating(self, value):
        self._avg_rating = value

    @property
    def unique_colors(self):
        """
        Retrieves unique active color variants for this product along with their images.
        Utilizes prefetched queries if active to avoid N+1 queries.
        """
        # Fetch variants list (using prefetch cache if available)
        if hasattr(self, '_prefetched_objects_cache') and 'variants' in self._prefetched_objects_cache:
            variants_list = self._prefetched_objects_cache['variants']
        else:
            variants_list = self.variants.filter(is_active=True)

        # Map color names to image URLs (using prefetch cache if available)
        color_imgs = {}
        if hasattr(self, '_prefetched_objects_cache') and 'variant_images' in self._prefetched_objects_cache:
            for vimg in self._prefetched_objects_cache['variant_images']:
                if vimg.image:
                    color_imgs[vimg.color] = vimg.image.url
        else:
            for vimg in self.variant_images.all():
                if vimg.image:
                    color_imgs[vimg.color] = vimg.image.url

        unique = []
        seen = set()
        for variant in variants_list:
            if variant.is_active and variant.color not in seen:
                seen.add(variant.color)
                img_url = color_imgs.get(variant.color)
                unique.append({
                    'color': variant.color,
                    'image_url': img_url or (self.image.url if self.image else ''),
                })
        return unique

    def __str__(self):
        return self.name



# =========================================================
# PRODUCT VARIANT IMAGE MODEL
# =========================================================

class ProductVariantImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variant_images'
    )
    color = models.CharField(max_length=50)
    image = CloudinaryField(
        'image',
        folder='products/variants/',
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ['product', 'color']

    def __str__(self):
        return f"{self.product.name} - {self.color} Image"


# =========================================================
# PRODUCT VARIANT MODEL
# =========================================================

class ProductVariant(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    SIZE_CHOICES = (
        # Alpha Sizes
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('2XL', '2XL'),
        ('3XL', '3XL'),
        ('5XL', '5XL'),
        # Numeric Sizes (Pants)
        ('28', '28'),
        ('30', '30'),
        ('32', '32'),
        ('34', '34'),
        ('36', '36'),
        ('40', '40'),
        ('42', '42'),
        ('44', '44'),
    )

    size = models.CharField(
        max_length=20,
        choices=SIZE_CHOICES,
        null=True,
        blank=True
    )

    color = models.CharField(max_length=50)

    stock = models.PositiveIntegerField(default=0)

    stock_status = models.CharField(
        max_length=20,
        choices=Product.STOCK_STATUS,
        default='IN_STOCK'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    allow_discount = models.BooleanField(default=True, verbose_name="Allow discount")

    @property
    def image(self):
        # Retrieve the image associated with the product and color from ProductVariantImage model
        variant_image = ProductVariantImage.objects.filter(product=self.product, color=self.color).first()
        return variant_image.image if variant_image else None

    @property
    def final_price(self):
        base_price = self.price if self.price else self.product.price
        if self.allow_discount and self.product.discount_price:
            discount_amount = self.product.price - self.product.discount_price
            if discount_amount > 0:
                return max(base_price - discount_amount, 0)
        return base_price

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Auto-correct stock status based on stock quantity to prevent validation crashes on excluded fields
        if self.stock <= 0:
            self.stock_status = 'OUT_OF_STOCK'
        elif self.stock < 5:
            self.stock_status = 'LIMITED'
        else:
            self.stock_status = 'IN_STOCK'

        p_type = self.product.product_type
        
        # Validation Rules
        rules = {
            'Shirt': ['M', 'L', 'XL', '2XL'],
            'Pant': ['28', '30', '32', '34', '36', '40', '42', '44'],
            'Shorts & Track': ['M', 'L', 'XL', '2XL', '3XL', '5XL'],
            'T-shirt': ['M', 'L', 'XL', '2XL', '3XL', '5XL'],
        }
        
        allowed = rules.get(p_type, [])
        if self.size not in allowed:
            raise ValidationError({
                'size': f"Size '{self.size}' is not valid for product type '{p_type}'. Valid sizes: {', '.join(allowed)}"
            })

    def save(self, *args, **kwargs):
        if self.stock <= 0:
            self.stock_status = 'OUT_OF_STOCK'
        elif self.stock < 5:
            self.stock_status = 'LIMITED'
        else:
            self.stock_status = 'IN_STOCK'
            
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['product', 'color', 'size']

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"


# =========================================================
# WISHLIST
# =========================================================

class Wishlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# =========================================================
# CART
# =========================================================

class Cart(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# =========================================================
# CART ITEM
# =========================================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE
    )

    size = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product_variant.final_price * self.quantity

    def __str__(self):
        return self.product_variant.product.name


# =========================================================
# ADDRESS
# =========================================================

class Address(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    full_name = EncryptedCharField()

    phone = EncryptedCharField()

    address_line = EncryptedTextField()

    city = EncryptedCharField()

    state = EncryptedCharField()

    country = EncryptedCharField()

    postal_code = EncryptedCharField()

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


# =========================================================
# ORDER
# =========================================================

class Order(models.Model):

    ORDER_STATUS = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    )

    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    )

    order_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    shipping_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='PENDING'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.order_id)


# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True
    )

    size = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return str(self.order.order_id)


# =========================================================
# PAYMENT
# =========================================================

class Payment(models.Model):

    PAYMENT_METHODS = (
        ('RAZORPAY', 'Razorpay'),
        ('STRIPE', 'Stripe'),
        ('COD', 'Cash On Delivery'),
    )

    PAYMENT_STATUS = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    payment_id = models.CharField(
        max_length=255,
        unique=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


# =========================================================
# REVIEWS / LIKES
# =========================================================

class Review(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comment = models.TextField(blank=True)

    likes = models.PositiveIntegerField(default=0)

    is_verified_purchase = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'user']

    def __str__(self):
        return self.product.name
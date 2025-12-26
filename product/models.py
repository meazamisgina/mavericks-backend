from django.db import models
from authentication.models import AppUser
from django.utils.text import slugify
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Audience(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'user_type': 'Seller'}
    )
    name = models.CharField(max_length=100, null=True, blank=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    audience = models.ForeignKey(Audience, on_delete=models.SET_NULL, null=True, related_name='products')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Condition(models.TextChoices):
        PREMIUM = 'Premium', 'No Flaws'
        GOOD = 'Good', 'Minor Wear'
        THRIFT = 'Thrift', 'Has Flaws (Mystery Box)'

    condition = models.CharField(
        max_length=20, 
        choices=Condition.choices, 
        default=Condition.PREMIUM
    )
    condition_notes = models.CharField(max_length=255, blank=True, null=True)



class MysteryBox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='mystery_boxes')
    name = models.CharField(max_length=100, default="Thrift Mystery Box")
    description = models.TextField(default="A curated collection of unique thrift finds.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    items = models.ManyToManyField(Product, related_name='contained_in_box')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} by {self.seller.email}"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Add a random string to the end of the name for the slug
            self.slug = slugify(self.name) + "-" + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

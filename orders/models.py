import uuid
from django.db import models
from authentication.models import AppUser
from cart.models import CartItem
from django.core.validators import MinValueValidator, MaxValueValidator

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processed', 'Processed'),
    ('cancelled', 'Cancelled'),
]

class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    product = models.ForeignKey(CartItem, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(1000000)],
        null=True,
        blank=True,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} by {self.buyer}"


   






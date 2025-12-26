import uuid
from django.db import models
from authentication.models import AppUser
from django.core.validators import MinValueValidator, MaxValueValidator
from product.models import Product, MysteryBox # Ensure MysteryBox is imported

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processed', 'Processed'),
    ('cancelled', 'Cancelled'),
]

class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    
    # Store the M-Pesa CheckoutRequestID for tracking payments
    mpesa_checkout_id = models.CharField(max_length=100, blank=True, null=True)
    
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
        return f"Order {self.order_id} by {self.buyer.email}"

    def update_total_price(self):
        """Calculates the total price from all order items (Products + Mystery Boxes)."""
        total = sum(item.subtotal for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    """Represents a single line item in an order, which can be a Product or a Mystery Box."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    
    # Allow either a Product OR a MysteryBox to be linked
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    mystery_box = models.ForeignKey(
        MysteryBox, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Historical price at the time of purchase
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])

    @property
    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        item_name = self.product.name if self.product else self.mystery_box.name
        return f"{self.quantity} of {item_name} in order {self.order.order_id}"
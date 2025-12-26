from django.db import models
import uuid
from django.conf import settings
from product.models import Product, MysteryBox # Import MysteryBox
from authentication.models import AppUser

class Cart(models.Model):
    cart_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        AppUser, on_delete=models.CASCADE, related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"Cart for {self.user.email}"

class CartItem(models.Model):
    cart_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    
    # Allow either a Product OR a MysteryBox
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    mystery_box = models.ForeignKey(MysteryBox, on_delete=models.CASCADE, null=True, blank=True)
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    added_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically set price based on which item type is present
        if self.product:
            self.unit_price = self.product.price
        elif self.mystery_box:
            self.unit_price = self.mystery_box.price
            
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.product.name if self.product else self.mystery_box.name
        return f"{self.quantity} of {name}"
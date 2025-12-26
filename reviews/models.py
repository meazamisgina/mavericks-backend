from django.db import models
import uuid
from authentication.models import AppUser
from orders.models import Order
from product.models import Product
from django.core.exceptions import ValidationError

class Review(models.Model):
    class Rating(models.IntegerChoices):
        ONE = 1, '1'
        TWO = 2, '2'
        THREE = 3, '3'
        FOUR = 4, '4'
        FIVE = 5, '5'

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    buyer = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Buyer'}
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(choices=Rating.choices)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # --- CHANGE 2: Ensure a buyer can only review a product once ---
        unique_together = ('buyer', 'product')
        ordering = ['-created_at']

    def clean(self):
        """Ensure the buyer has purchased the product they are reviewing."""
        if not Order.objects.filter(buyer=self.buyer, items__product=self.product, status='processed').exists():
            raise ValidationError("You can only review products you have purchased and received.")

    def __str__(self):
        return f"Review for {self.product.name} by {self.buyer.email}"


class RateTrader(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    buyer = models.ForeignKey(
        AppUser,
        related_name='given_ratings',
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Buyer'}
    )
    seller = models.ForeignKey(
        AppUser,
        related_name='received_ratings',
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Seller'}
    )
    rating = models.IntegerField(choices=Review.Rating.choices) # Reuse choices from Review
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # --- CHANGE 4: Ensure a buyer can only rate a seller once ---
        unique_together = ('buyer', 'seller')
        ordering = ['-created_at']

    def clean(self):
        # --- CHANGE 5: Prevent users from rating themselves ---
        if self.buyer == self.seller:
            raise ValidationError("A user cannot rate themselves.")

    def __str__(self):
        return f"Rating for {self.seller.email} by {self.buyer.email}"
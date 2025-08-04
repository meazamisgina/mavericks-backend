from django.db import models
import uuid
from authentication.models import AppUser
from product.models import Product

class Review(models.Model):
    review_id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    buyer = models.ForeignKey(AppUser, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        null=False
    )
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review {self.review_id} by {self.buyer}"


class RateTrader(models.Model):
    rate_trader_id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    buyer = models.ForeignKey(AppUser, related_name='buyer_ratings', on_delete=models.CASCADE, null=True, blank=True)
    seller = models.ForeignKey(AppUser, related_name='seller_ratings', on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        null=False
    )
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trader Rating {self.rate_trader_id} from {self.buyer} to {self.seller}"
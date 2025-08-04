from django.contrib import admin
from .models import Review, RateTrader
from .models import Product

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'buyer', 'product', 'rating', 'created_at')
    search_fields = ('buyer__username', 'product__name', 'rating')
    list_filter = ('rating', 'created_at')

@admin.register(RateTrader)
class RateTraderAdmin(admin.ModelAdmin):
    list_display = ('rate_trader_id', 'buyer', 'seller', 'rating', 'created_at')
    search_fields = ('buyer__username', 'seller__username', 'rating')
    list_filter = ('rating', 'created_at')

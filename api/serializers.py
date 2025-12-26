from rest_framework import serializers
from product.models import Product, Category, Audience, Size, MysteryBox
from orders.models import Order, OrderItem
from reviews.models import Review, RateTrader
from cart.models import Cart, CartItem
from authentication.models import AppUser



# ===================================================================
# User Serializers
# ===================================================================

class AppUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom AppUser model. Handles user registration and display.
    The password is write-only for security.
    """
    class Meta:
        model = AppUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone', 'user_type', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def create(self, validated_data):
        # Use the create_user method to properly hash the password.
        user = AppUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'Buyer'), # Default to Buyer
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone')
        )
        return user


# ===================================================================
# Product and Category Serializers
# ===================================================================

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.
    Uses StringRelatedField for readable representations of foreign keys.
    """
    # Make foreign key fields readable
    seller = serializers.StringRelatedField(read_only=True)
    category = serializers.StringRelatedField()
    audience = serializers.StringRelatedField()
    size = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock_quantity',
            'image', 'seller', 'category', 'audience', 'size',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'category': {'required': False, 'allow_null': True}, # Optional: if you want AI to pick category too
        }
        read_only_fields = ['slug', 'seller', 'created_at', 'updated_at']



class MysteryBoxSerializer(serializers.ModelSerializer):
    # This nesting shows you the full details of the items inside the box
    items = ProductSerializer(many=True, read_only=True)
    seller_email = serializers.ReadOnlyField(source='seller.email')

    class Meta:
        model = MysteryBox
        fields = [
            'id', 'name', 'description', 'price', 
            'items', 'seller_email', 'is_active', 'created_at'
        ]

# ===================================================================
# Cart and CartItem Serializers
# ===================================================================

class CartItemSerializer(serializers.ModelSerializer):
    # Nest a simplified product serializer for better detail in the cart view
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True) # For adding items to cart

    class Meta:
        model = CartItem
        fields = ['cart_item_id', 'product', 'product_id', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['cart_item_id', 'unit_price', 'subtotal', 'product']

class CartSerializer(serializers.ModelSerializer):
    # Use the CartItemSerializer to show a list of items in the cart
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['cart_id', 'user', 'items', 'total_price', 'updated_at']
        read_only_fields = ['user']


# ===================================================================
# Order and OrderItem Serializers
# ===================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for a single item within an order."""
    product = ProductSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    """
    Main serializer for an Order. It includes nested OrderItems
    to show a complete picture of the order.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    buyer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['order_id', 'buyer', 'status', 'total_price', 'items', 'created_at']


# ===================================================================
# Offer, Discount, and Review Serializers
# ===================================================================

# class OfferSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Offer
#         fields = '__all__'

# class DiscountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Discount
#         fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Review
        fields = ['id', 'buyer', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'buyer', 'created_at']

    def validate(self, data):
        """
        Check that the user has purchased the product before reviewing.
        """
        request = self.context['request']
        product = data['product']
        buyer = request.user

        if not Order.objects.filter(buyer=buyer, items__product=product, status='processed').exists():
            raise serializers.ValidationError("You can only review products you have purchased and received.")

        return data

class RateTraderSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField(read_only=True)
    seller = serializers.PrimaryKeyRelatedField(queryset=AppUser.objects.filter(user_type='Seller'))

    class Meta:
        model = RateTrader
        fields = ['id', 'buyer', 'seller', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'buyer', 'created_at']

    def validate(self, data):
        """
        Check that a user is not rating themselves.
        """
        request = self.context['request']
        if request.user == data['seller']:
            raise serializers.ValidationError("You cannot rate yourself.")
        return data
    

# api/serializers.py
class MpesaSTKPushInitiateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=12)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    reference = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(max_length=255, required=False)

    def validate_phone_number(self, value):
        # Ensure it starts with 254
        if not value.startswith('254') or len(value) != 12:
            raise serializers.ValidationError("Use format 2547XXXXXXXX")
        return value

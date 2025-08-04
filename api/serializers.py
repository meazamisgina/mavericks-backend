from rest_framework import serializers
from product.models import Product
from orders.models import Order
from offer.models import Offer, Discount
from reviews.models import Review, RateTrader
from cart.models import Cart, CartItem
from django.contrib.auth.models import User as AuthUser
from authentication.models import AppUser
from django.contrib.auth.models import User as AuthUser
from .models import AppUser

from rest_framework import serializers
from .models import Order
from authentication.models import AppUser
from cart.models import CartItem



class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['product', 'quantity', 'status'] 

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive integer.")
        return value

    def create(self, validated_data):
        order = Order.objects.create(**validated_data)
        return order

    def update(self, instance, validated_data):
        instance.product = validated_data.get('product', instance.product)
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'  

    def create(self, validated_data):
        user = self.context['request'].user
        app_user = AppUser.objects.get(user=user)  
        validated_data['buyer'] = app_user
        return super().create(validated_data)



class AuthUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = AuthUser 
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = AuthUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user
    def validate_email(self, value):
        if AuthUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value


class AppUserSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()

    class Meta:
        model = AppUser
        fields = ['user','id', 'name', 'phone', 'user_type']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        auth_user_serializer = self.fields['user']
        auth_user_instance = auth_user_serializer.create(user_data)
        app_user = AppUser.objects.create(user=auth_user_instance, **validated_data)
        return app_user




class ProductSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class RateTraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateTrader
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'


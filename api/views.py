from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from product.models import Product
from orders.models import Order, OrderItem, STATUS_CHOICES
from rest_framework import viewsets, generics, permissions, status, serializers
from rest_framework.permissions import IsAuthenticated
from reviews.models import Review, RateTrader
from cart.models import Cart, CartItem
from authentication.models import AppUser
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .chat_utils import shopping_agent
from .ai_utils import ai_brain
from product.models import Category, Audience, Product, Size, MysteryBox
from django.shortcuts import get_object_or_404
from .vector_utils import add_product_to_vector_db, search_similar_products
from payments.mpesa_api import MpesaAPIClient
from payments.models import MpesaSTKPush
from .serializers import MpesaSTKPushInitiateSerializer
from .serializers import (
    OrderSerializer,
    ProductSerializer,
    ReviewSerializer,
    RateTraderSerializer,
    CartSerializer,
    CartItemSerializer,
    AppUserSerializer,
    MysteryBoxSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime
import logging

from payments.mpesa_api import MpesaAPIClient
from payments.models import MpesaSTKPush
from .serializers import MpesaSTKPushInitiateSerializer
from .permissions import IsSellerOrReadOnly, IsOwnerOrAdmin


# ===================================================================
# Authentication Views
# ===================================================================

class AppUserViewSet(viewsets.ModelViewSet):
    queryset = AppUser.objects.all()
    serializer_class = AppUserSerializer
    # Only admins should be able to list/manage all users
    permission_classes = [permissions.IsAdminUser]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Users now log in with email, as defined in the AppUser model
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using the custom user model
        user = authenticate(request=request, email=email, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type # user_type is now directly on the user model
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Use the main AppUserSerializer for registration
        serializer = AppUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Automatically create a cart for the new user
            Cart.objects.create(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Simply delete the token to force a login
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================================================
# Core E-commerce Views
# ===================================================================

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Buyers see their own orders.
        Sellers see orders containing their products.
        """
        user = self.request.user
        if user.user_type == 'Buyer':
            # Correctly filter by the buyer field on the Order model
            return Order.objects.filter(buyer=user).order_by('-created_at')
        elif user.user_type == 'Seller':
            # Find orders that have items where the product's seller is the current user
            return Order.objects.filter(items__product__seller=user).distinct().order_by('-created_at')
        return Order.objects.none() # Return nothing if user type is not set

    def create(self, request, *args, **kwargs):
        """Create an order from the user's cart."""
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        cart_items = cart.items.all()

        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the order
        order = Order.objects.create(buyer=user, total_price=cart.total_price)

        # Create order items from cart items
        order_items_to_create = []
        for cart_item in cart_items:
            order_items_to_create.append(
                OrderItem(order=order, product=cart_item.product, quantity=cart_item.quantity, price=cart_item.product.price)
            )
        OrderItem.objects.bulk_create(order_items_to_create)

        # Clear the cart
        cart_items.delete()

        # Serialize the newly created order and return it
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # This method is now bypassed by the custom create method above.
        # We leave it empty or pass, as it's not used for creating orders from carts.
        pass

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Allows a seller to update the status of an order."""
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status and new_status in dict(STATUS_CHOICES).keys():
            # Check if the user is a seller for at least one item in the order
            if not order.items.filter(product__seller=request.user).exists():
                return Response({"detail": "You are not the seller for any item in this order."}, status=status.HTTP_403_FORBIDDEN)

            order.status = new_status
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid status or status not provided."}, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsSellerOrReadOnly]

    def perform_create(self, serializer):
        # 1. Initial save to store image
        product = serializer.save(seller=self.request.user)
        
        if product.image:
            try:
                # 2. AI Analysis (Description, Name, Category, Size)
                ai_data = ai_brain.analyze_product_image(product.image.path)
                
                if ai_data:
                    # Auto-Name logic
                    generic_names = ['t-shirt', 'item', 'product', 'clothes', 'jacket']
                    if not product.name or product.name.lower() in generic_names:
                        product.name = ai_data.get('product_name', product.name)

                    product.description = ai_data.get('description', product.description)
                    product.condition = ai_data.get('condition', product.condition)
                    product.condition_notes = ai_data.get('condition_notes', 'No defects')

                    # Auto-Link Category
                    cat_name = ai_data.get('category')
                    if cat_name:
                        cat_obj, _ = Category.objects.get_or_create(name=cat_name.title())
                        product.category = cat_obj

                    # Auto-Link Audience
                    aud_name = ai_data.get('audience')
                    if aud_name:
                        aud_obj, _ = Audience.objects.get_or_create(name=aud_name.title())
                        product.audience = aud_obj

                    # Auto-Link Size
                    sz_name = ai_data.get('size')
                    if sz_name:
                        sz_obj, _ = Size.objects.get_or_create(name=sz_name.upper())
                        product.size = sz_obj

                    # Save database fields
                    product.save()

                    # 3. ADD TO VISUAL SEARCH MEMORY
                    add_product_to_vector_db(
                        product_id=product.id,
                        image_path=product.image.path,
                        metadata={
                            "name": str(product.name),
                            "price": float(product.price),
                            "condition": str(product.condition)
                        }
                    )
                    
                    # 4. MYSTERY BOX BUNDLING LOGIC (The New Part)
                    if product.condition == 'Thrift':
                        # Find other 'Thrift' items by this seller not in a box
                        loose_thrift_items = Product.objects.filter(
                            seller=self.request.user,
                            condition='Thrift',
                            contained_in_box__isnull=True
                        ).exclude(id=product.id)

                        # Bundle if we have 3 or more
                        if loose_thrift_items.count() >= 2:
                            items_for_box = list(loose_thrift_items[:2]) + [product]
                            total_value = sum(item.price for item in items_for_box)

                            bundle_price = float(total_value) * 0.60

                            new_box = MysteryBox.objects.create(
                                seller=self.request.user,
                                price=bundle_price,
                                description=f"Bulk Thrift Bundle: 3 items for the price of one! Total value was {total_value} KES."
                            )
                            # # Link the first 3 items to this box
                            new_box.items.set(loose_thrift_items[:3])
                            new_box.save()
                            print(f"DEBUG: Mystery Box created at discounted price: {bundle_price} KES")

                    print(f"DEBUG: {product.name} processed successfully.")
                    
            except Exception as e:
                print(f"DEBUG Error in Product Creation Flow -> {e}")

    @action(detail=False, methods=['post'], url_path='search-by-image')
    def search_by_image(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({"error": "No image provided"}, status=400)

        temp_path = "temp_search.jpg"
        with open(temp_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        try:
            results = search_similar_products(temp_path)
            product_ids = results['ids'][0]
            products = Product.objects.filter(id__in=product_ids)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": f"Search failed: {str(e)}"}, status=500)

# ===================================================================
# Other Generic Views
# ===================================================================

# class OfferViewSet(viewsets.ModelViewSet):
#     queryset = Offer.objects.all()
#     serializer_class = OfferSerializer
# class DiscountViewSet(viewsets.ModelViewSet):
#     queryset = Discount.objects.all()
#     serializer_class = DiscountSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set the buyer to the currently authenticated user
        serializer.save(buyer=self.request.user)

class RateTraderViewSet(viewsets.ModelViewSet):
    queryset = RateTrader.objects.all()
    serializer_class = RateTraderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set the buyer to the currently authenticated user
        serializer.save(buyer=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """A user can only see their own cart."""
        return Cart.objects.filter(user=self.request.user)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """A user can only see items in their own cart."""
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        """Add an item to the user's cart."""
        cart = get_object_or_404(Cart, user=self.request.user)
        serializer.save(cart=cart)

class MysteryBoxViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing mystery boxes. 
    We use ReadOnly because boxes are created automatically by AI.
    """
    queryset = MysteryBox.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = MysteryBoxSerializer



mpesa_client = MpesaAPIClient()

class InitiateSTKPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MpesaSTKPushInitiateSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            amount = serializer.validated_data['amount']
            
            try:
                # 1. Start the M-Pesa push
                daraja_response = mpesa_client.initiate_stk_push(
                    phone_number=phone_number,
                    amount=amount,
                    reference=f"User-{request.user.id}",
                    description="Gikomba Purchase"
                )

                # 2. Record it in your MpesaSTKPush model
                MpesaSTKPush.objects.create(
                    user=request.user,
                    phone_number=phone_number,
                    amount=amount,
                    checkout_request_id=daraja_response.get('CheckoutRequestID'),
                    status='Pending'
                )

                return Response({"message": "Payment initiated!"})
            except Exception as e:
                return Response({"error": str(e)}, status=500)
        return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mpesa_callback(request):
    # (The callback logic we discussed previously)
    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

class ChatAssistantView(APIView): # The new Chat view
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message')
        ai_response = shopping_agent.ask_agent(user_message)
        return Response({"reply": ai_response})



class ChatAssistantView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": "Sema kitu (Say something)!"}, status=400)
            
        ai_response = shopping_agent.ask_agent(user_message, request.user.username)
        return Response({"reply": ai_response})
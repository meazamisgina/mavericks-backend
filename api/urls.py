from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    OrderViewSet,
    RegisterView,
    LoginView,
    LogoutView,
    ReviewViewSet,  
    RateTraderViewSet,  
    CartViewSet,  
    CartItemViewSet, 
    AppUserViewSet,
    MysteryBoxViewSet,
    ChatAssistantView,
    InitiateSTKPushView,
    mpesa_callback,
    ChatAssistantView,  
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'users', AppUserViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet)
router.register(r'rate-traders', RateTraderViewSet)
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cartitem')
router.register(r'mystery-boxes', MysteryBoxViewSet)

urlpatterns=[
    path('', include(router.urls)),
    path('chat/', ChatAssistantView.as_view(), name='chat_assistant'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('payments/stk-push/', InitiateSTKPushView.as_view(), name='initiate_stk_push'),
    path('payments/callback/', mpesa_callback, name='mpesa_callback')
]

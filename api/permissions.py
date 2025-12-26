from rest_framework import permissions

class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow sellers to create/edit objects.
    Read-only access is allowed for anyone.
    """
    def has_permission(self, request, view):
        # Allow all safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # For unsafe methods (POST, PUT, PATCH, DELETE), user must be an authenticated seller.
        return request.user and request.user.is_authenticated and request.user.user_type == 'Seller'

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    Assumes the model instance has a `user` or `buyer` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin users have full access.
        if request.user.is_staff:
            return True

        # Check if the object's owner matches the request user.
        # This flexibly checks for 'user' or 'buyer' fields.
        return (hasattr(obj, 'user') and obj.user == request.user) or \
               (hasattr(obj, 'buyer') and obj.buyer == request.user)

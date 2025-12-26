from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppUser


@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    """
    Admin configuration for the custom AppUser model.
    Inherits from UserAdmin to get all the standard user management features.
    """
    # Fields to display in the user list view.
    # These fields now correctly reference the AppUser model.
    list_display = ('email', 'username', 'user_type', 'is_staff', 'date_joined')
    
    # Fields to use for searching.
    search_fields = ('email', 'username')
    
    # Fields to use for filtering in the admin sidebar.
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'groups')
    
    # The fieldsets for the user edit form.
    # We add 'user_type' and 'phone' to the standard fields.
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Info', {'fields': ('user_type', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Info', {'fields': ('user_type', 'phone')}),
    )

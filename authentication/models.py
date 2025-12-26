from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid

class AppUser(AbstractUser):
    """
    Custom user model that serves as the single source of truth for users.
    It inherits from Django's AbstractUser, gaining all standard auth fields,
    and adds specific fields for this application like user_type and phone.
    """
    class UserType(models.TextChoices):
        BUYER = 'Buyer', _('Buyer')
        SELLER = 'Seller', _('Seller')

    # Use UUID as the primary key for better security and scalability.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Inherits username, first_name, last_name, password, is_staff, etc.
    # from AbstractUser.

    # Override email to be unique and serve as the main identifier for login.
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.BUYER,
        help_text="Designates the user's role in the application."
    )

    # Use 'email' for authentication instead of 'username'.
    USERNAME_FIELD = 'email'
    
    # A list of the field names that will be prompted for when creating a user
    # via the `createsuperuser` management command. 'username' is required
    # here because it's not the USERNAME_FIELD but is still a required field
    # on the base AbstractUser model.
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

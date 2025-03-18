from django.db import models
from django.core.validators import RegexValidator
import random
import string
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# -----------------------------------------------------------------------------
# Utility Function
# -----------------------------------------------------------------------------
def generate_referral_code(user_id):
    """
    Generate a unique referral code based on user_id.
    """
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"USER{user_id}{random_str}"


# -----------------------------------------------------------------------------
# Custom User Manager
# -----------------------------------------------------------------------------
class UserManager(BaseUserManager):
    def create_user(self, username, emailid, firstname, lastname, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")
        if not emailid:
            raise ValueError("The Email must be set")
        emailid = self.normalize_email(emailid)
        user = self.model(
            username=username,
            emailid=emailid,
            firstname=firstname,
            lastname=lastname,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, emailid, firstname, lastname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, emailid, firstname, lastname, password, **extra_fields)


# -----------------------------------------------------------------------------
# Custom User Model
# -----------------------------------------------------------------------------
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that stores user information along with referral features.
    """
    userid = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    emailid = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)  # Store hashed password here
    contactnumber = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    gender = models.CharField(max_length=10)
    createdat = models.DateField(auto_now_add=True)
    lastlogin = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='active')
    subscription = models.CharField(max_length=50, default="unsubscribed")
    referral_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=100, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_users",
        db_column='referred_by'
    )
    # Required attributes for Django custom user model
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['emailid', 'firstname', 'lastname']

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """
        Overridden save method to generate a referral code if not already set.
        We call super().save() to make sure the instance gets a primary key before generation.
        Then we update only the referral_code field using the queryset update to prevent recursion.
        """
        new_instance = self.pk is None
        super().save(*args, **kwargs)
        if not self.referral_code:
            self.referral_code = generate_referral_code(self.userid)
            User.objects.filter(pk=self.pk).update(referral_code=self.referral_code)


# -----------------------------------------------------------------------------
# Profile Model
# -----------------------------------------------------------------------------
class Profile(models.Model):
    """
    Profile model extends the default information stored for a user.
    Contains additional data such as location, balance credits, bio, and an avatar.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100, blank=True)
    balance_credits = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# -----------------------------------------------------------------------------
# Admin Model
# -----------------------------------------------------------------------------
class Admin(models.Model):
    """
    Model for administrative users.
    Stores admin-specific data with phone number validation.
    """
    adminid = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=25)
    lastname = models.CharField(max_length=25)
    emailid = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Supports storing hashed passwords
    contactnumber = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")]
    )
    address = models.TextField()
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    createdat = models.DateField(auto_now_add=True)
    lastlogin = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='active')
    gender = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "admin"

    def __str__(self):
        return self.emailid

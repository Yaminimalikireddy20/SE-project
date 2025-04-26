from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now
import uuid  # For generating unique reset tokens
import logging
from .models import User, Profile
from base64 import b64encode
from django.utils.encoding import force_str


# Temporary storage for reset tokens (production should use a database or cache)
reset_tokens = {}

logger = logging.getLogger(__name__)

# -------------------- Authentication and Profile Management -------------------- #
@csrf_protect

def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')
        user = User.objects.filter(username=identifier).first() or User.objects.filter(emailid=identifier).first()

        if user and user.check_password(password):
            login(request, user)
            
            # Fetch avatar base64 for the session
            profile = Profile.objects.filter(user=user).first()
            avatar_base64 = None
            if profile and profile.avatar:
                avatar_base64 = b64encode(profile.avatar).decode('utf-8')
            request.session['avatar_base64'] = avatar_base64  # Store base64 in session
            
            messages.success(request, "Login successful!")
            return redirect('user_dashboard')

        else:
            messages.error(request, "Invalid credentials.")
            return redirect('loginpage')

    return render(request, 'login.html')

# Signal to automatically create a Profile for new users
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except AttributeError:
        # Handle case where Profile doesn't exist
        logger.warning("User %s does not have a profile.", instance.userid)



@login_required
def user_profile(request, user_id):
    """
    View and manage the user's profile based on user_id.
    """
    user = get_object_or_404(User, userid=user_id)
    profile, created = Profile.objects.get_or_create(user=user)  # Create Profile if it doesn't exist

    if request.method == 'POST':
        # Update profile fields
        profile.location = request.POST.get('location', profile.location)
        profile.balance_credits = request.POST.get('balance_credits', profile.balance_credits)
        profile.bio = request.POST.get('bio', profile.bio)

        # Handle avatar upload and store it as binary
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            if hasattr(avatar_file, 'read'):  # Ensure it's file-like
                profile.avatar = avatar_file.read()  # Save binary content
            else:
                messages.error(request, "Invalid avatar file uploaded.")

        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('user_profile', user_id=user.userid)

    # Convert binary image to base64 string for display
    avatar_base64 = None
    if profile.avatar:
        avatar_base64 = b64encode(profile.avatar).decode('utf-8')

    return render(request, 'user_profile.html', {
        'profile': profile,
        'user': user,
        'avatar_base64': avatar_base64
    })

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Profile

@login_required
def delete_avatar(request):
    """
    Delete the avatar from the user's profile.
    """
    profile = get_object_or_404(Profile, user=request.user)
    if profile.avatar:
        profile.avatar = None  # Remove the avatar
        profile.save()
        messages.success(request, "Your avatar has been deleted successfully.")
    else:
        messages.warning(request, "No avatar to delete.")
    return redirect('user_profile', user_id=request.user.userid)


@login_required
def delete_avatar(request):
    """
    Delete the avatar from the user's profile.
    """
    profile = get_object_or_404(Profile, user=request.user)
    if profile.avatar:
        profile.avatar = None  # Remove the avatar
        profile.save()
        messages.success(request, "Your avatar has been deleted successfully.")
    else:
        messages.warning(request, "No avatar to delete.")
    return redirect('user_profile', user_id=request.user.userid)

@login_required
def user_dashboard_view(request):
    """
    Display referral points in the dashboard.
    """
    referral_points = request.user.referral_points
    return render(request, 'user_dashboard.html', {'referral_points': referral_points})

# -------------------- Password Reset Functionality -------------------- #

def password_reset_request(request):
    """
    Handles password reset requests and sends a reset link via email.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            try:
                user = User.objects.get(emailid=email)
                token = str(uuid.uuid4())  # Generate unique reset token
                reset_tokens[token] = {'user_id': user.userid, 'expires_at': now()}

                # Create and send password reset link
                reset_link = request.build_absolute_uri(reverse("password_reset_confirm", args=[token]))
                send_mail(
                    subject="Password Reset Request",
                    message=f"Click the link below to reset your password:\n\n{reset_link}",
                    from_email="noreply@indoorsports.com",
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "Password reset link has been sent to your email.")
            except User.DoesNotExist:
                messages.error(request, "Email not found. Please provide a valid email.")
        else:
            messages.error(request, "Email field cannot be empty.")
    return render(request, "password_reset.html")

def password_reset_confirm(request, token):
    """
    Handles password reset confirmation and allows user to set a new password.
    """
    token_data = reset_tokens.get(token)
    # Validate token expiration (1 hour)
    if not token_data or (now() - token_data['expires_at']).total_seconds() > 3600:
        messages.error(request, "Invalid or expired token.")
        reset_tokens.pop(token, None)  # Cleanup invalid token
        return redirect("password_reset")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            user = User.objects.get(userid=token_data['user_id'])
            user.password = make_password(new_password)  # Securely hash the new password
            user.save()
            messages.success(request, "Password reset successfully. You can now log in.")
            reset_tokens.pop(token, None)  # Cleanup token
            return redirect("loginpage")
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, "password_reset_confirm.html", {"token": token})


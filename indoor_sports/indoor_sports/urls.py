"""
URL configuration for indore_sports project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    
    # Core apps and functionalities provided by different teams:
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('reports/', include('reports.urls')),
    path('equipment/', include('equipment.urls')),
    path('ratings/', include('ratings.urls')),
    path('register/', include('registration.urls')),
    path('login/', include('login.urls')),
    path('payments/', include('payments.urls')),
    path('my_referrals/', include('my_referrals.urls')),  # Using underscore as per project structure
    path('dashboards/', include('dashboards.urls')),
    
    # Additional functionalities from the first snippet:
    path('sports/', include('sports.urls')),
    path('memberships/', include('memberships.urls')),
    path('notifications/', include('notifications.urls')),
    path('', include('accounts.urls')),  # Include login and logout views, if defined in accounts app

    
    # Redirect the root URL directly to the login page.
    path('', lambda request: redirect('loginpage')),  # 'loginpage' must match the URL name defined in login.urls
]

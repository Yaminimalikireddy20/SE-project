from django.urls import path
from . import views

urlpatterns = [
    path('weekly/', views.weekly_report, name='weekly_report'),
    path('monthly/', views.monthly_report, name='monthly_report'),
    path('yearly/', views.yearly_report, name='yearly_report'),
]

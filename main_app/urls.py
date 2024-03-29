from django.urls import path
from . import views


urlpatterns = [
    path('products/', views.get_products, name='get_products'),
    path('products/signup/<str:product_id>/', views.signup_for_course, name='signup_for_course'),
    path('products/stats/', views.get_stats, name='get_stats'),
    path('lessons/<str:product_id>/', views.get_available_lessons, name='get_available_lessons'),
]
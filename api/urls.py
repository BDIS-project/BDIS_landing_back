from django.urls import path
from .views import * 
from rest_framework_simplejwt import views as jwt_views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products', ProductsAPIView.as_view(), name = 'products'),
    path('store-products', StoreProductsAPIView.as_view(), name='store-products'),
    path('categories', CategoriesAPIView.as_view(), name='get_categories'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

from django.urls import path
from .views import * 
from rest_framework_simplejwt import views as jwt_views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products', StoreProducts2APIView.as_view(), name='store-products'),
    path('categories', CategoriesAPIView.as_view(), name='get_categories'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
]

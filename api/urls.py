from django.urls import path
from api.views import * 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products/', ProductsAPIView.as_view(), name = 'products'),
    path('store-products/', StoreProductsAPIView.as_view(), name='store-products'),
    path('categories/', CategoriesAPIView.as_view(), name='get_categories'),
    
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('test-token/', TestTokenView.as_view(), name='test_token'),
]

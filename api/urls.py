from django.urls import path
from . import views # for views.get_schedule?
from .views import * # for ScheduleAPIView?
from rest_framework_simplejwt import views as jwt_views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('categories/', CategoriesAPIView.as_view(), name='get_categories'),
    path('categories/<int:category_number>/updateCategory/', CategoriesAPIView.as_view(), name='update_category'),

    path('products/', ProductsAPIView.as_view(), name='get_products'),
    path('products/<int:id_product>/updateProduct/', ProductsAPIView.as_view(), name='update_product'),

    path('store-products', StoreProductsAPIView.as_view(), name='store-products'),
    #path('store-products/<str:UPC>/updateStoreProduct/', StoreProductsAPIView.as_view(), name='update_store-products'),

    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('store-overview/', StoreOverviewAPIView.as_view(), name = 'store-overview'),
    path('check-overview', CheckOverviewAPIView.as_view(), name = 'check-overview'),
    path('customer-card-overview', CustomerCardOverviewAPIView.as_view(), name = 'customer-card-overview'),
    path('manager-store-overview', ManagerStoreOverviewAPIView.as_view(), name = 'manager-store-overview'),
    
]

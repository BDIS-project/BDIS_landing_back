from django.urls import path
from . import views # for views.get_schedule?
from .views import * # for ScheduleAPIView?
from rest_framework_simplejwt import views as jwt_views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products', ProductsAPIView.as_view(), name = 'products'),
    path('store-products', StoreProductsAPIView.as_view(), name='store-products'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('store-overview/', StoreOverviewAPIView.as_view(), name = 'store-overview'),
    path('check-overview', CheckOverviewAPIView.as_view(), name = 'check-overview'),
    path('categories', CategoriesAPIView.as_view(), name='get_categories'),
    path('product-names', ProductNamesAPIView.as_view(), name = 'product-names'),

    path('create-category', CreateCategoryAPIView.as_view(), name = 'create-category'),
    path('create-product', CreateProductAPIView.as_view(), name = 'create-product'),
    path('create-store-product', CreateStoreProductAPIView.as_view(), name = 'create-store-product'),
    path('create-employee', CreateEmployeeAPIView.as_view(), name = 'create-employee'),
    path('create-customer', CreateCustomerAPIView.as_view(), name = 'create-customer'),
    path('delete-category', DeleteCategoryAPIView.as_view(), name = 'delete-category'),

    path('delete-product/<int:id_product>/', DeleteCProductAPIView.as_view(), name = 'delete-product'),
    path('delete-store-product', DeleteStoreProductAPIView.as_view(), name = 'delete-store-product'),
    path('delete-employee', DeleteEmployeeAPIView.as_view(), name = 'delete-employee'),
    path('delete-customer', DeleteCustomerAPIView.as_view(), name = 'delete-customer'),
]

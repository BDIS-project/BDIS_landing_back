from django.urls import path
from . import views # for views.get_schedule?
from .views import * # for ScheduleAPIView?
from rest_framework_simplejwt import views as jwt_views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products/', StoreProductsAPIView.as_view(), name='store-products'),
]

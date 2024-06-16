from django.urls import path
from . import views # for views.get_schedule?
from .views import * # for ScheduleAPIView?
from rest_framework_simplejwt import views as jwt_views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products', StoreProducts2APIView.as_view(), name='store-products'),
    path('categories', CategoriesAPIView.as_view(), name='get_categories'),
]

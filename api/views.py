from rest_framework import generics, permissions
from rest_framework.response import Response
#from .models import Category, Product, StoreProduct, Employee, Check, CustomerCard, Sale
#from .serializers import *

class StoreProductsAPIView(generics.ListAPIView):
    """

    """
    def get_parameters(self):
        return
    def get_queryset(self): 
        return
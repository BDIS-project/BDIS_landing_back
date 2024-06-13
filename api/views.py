from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db import connection
from rest_framework.views import APIView
#from .models import Category, Product, StoreProduct, Employee, Check, CustomerCard, Sale
#from .serializers import *

class StoreProductsAPIView(APIView):
    """
    API view to retrieve store products using raw SQL.
    """

    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT Store_Product.id_product, product_name, selling_price, products_number, promotional_product "+
                           "FROM Store_Product INNER JOIN Product ON Store_Product.id_product = Product.id_product "+
                           "ORDER BY products_number;")
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]
        print(result)

        return Response(result)
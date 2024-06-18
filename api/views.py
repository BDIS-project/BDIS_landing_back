from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
#from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from types import SimpleNamespace

from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import hashlib

import logging

from api.permissions import (
    IsAuthenticated,
    AllowAny,
    IsCashier, 
    IsManager, 
    IsCashierOrManager 
)

class StoreProductsAPIView(APIView):
    permission_classes = [IsCashierOrManager]
    """
    API view to retrieve store products using raw SQL.
    """
    def get(self, request, *args, **kwargs):
        
        upc = request.GET.get('upc')
        product_name = request.GET.get('product_name')
        promotional = request.GET.get('promotional')
        min_price = request.GET.get('minPrice')
        max_price = request.GET.get('maxPrice')
        categories = request.GET.get('categories')
        in_stock = request.GET.get('inStock')
        sort_by = request.GET.get('sort')

        query_conditions = []
        params = []

        if sort_by:
            sorter = ''
            if sort_by == 'products-desc':
                sorter = "product_name DESC"
            elif sort_by == 'products-asc':
                sorter = "product_name "
            elif sort_by == 'price-desc':
                sorter = "selling_price DESC"
            elif sort_by == 'price-asc':
                sorter = "selling_price "
            elif sort_by == 'numbers-desc':
                sorter = "product_numbers DESC "
            else:
                sorter = "product_numbers "
           
        base_query = (
            "SELECT Store_Product.*, product_name, category_name "
            "FROM Store_Product "
            "INNER JOIN Product ON Store_Product.id_product = Product.id_product "
            "INNER JOIN Category ON Product.category_number = Category.category_number "
            "WHERE 1=1 "
        )

        query_conditions = []
        params = []

        if upc:
            query_conditions.append("AND UPC = %s")
            params.append(upc)
        if product_name:
            query_conditions.append("AND product_name LIKE %s")
            params.append(product_name)
        if promotional:
            query_conditions.append("AND promotional_product = %s")
            params.append(promotional.lower() == 'true')
        if min_price:
            query_conditions.append("AND selling_price >= %s")
            params.append(min_price)
        if max_price:
            query_conditions.append("AND selling_price <= %s")
            params.append(max_price)
        if categories:
            category_list = categories.split(',')
            query_conditions.append(f"AND category_name IN ({','.join(['%s'] * len(category_list))})")
            params.extend(category_list)
        if in_stock:
            query_conditions.append("AND products_number > 0")

        query = base_query + ' '.join(query_conditions) + ";"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = []
        for row in rows:
            product = dict(zip(columns, row))
            if 'promotional_product' in product and product['promotional_product']:
                product['original_price'] = round(float(product['selling_price']) / 0.8, 2)
            if 'selling_price' in product:
                product['selling_price'] = round(float(product['selling_price']), 2)
            result.append(product)

        return Response(result, status=status.HTTP_200_OK)


class CategoriesAPIView(APIView):
    permission_classes = [IsCashierOrManager]
    """
    API view to retrieve all categories using raw SQL.
    """
    def get(self, request, *args, **kwargs):
        query = "SELECT category_name FROM Category ORDER BY category_name;"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        category_names = [row[0] for row in rows]

        return Response(category_names, status=status.HTTP_200_OK)


class ProductsAPIView(APIView):
    permission_classes = [IsCashierOrManager]
    """
    API view to retrive products using raw sql
    """
    def get(self, request, *args, **kwargs):
        query = ("SELECT Store_Product.*, product_name, category_name "
                "FROM Store_Product INNER JOIN Product ON Store_Product.id_product = Product.id_product "
                "INNER JOIN Category ON Product.category_number = Category.category_number "
                "ORDER BY product_name;")
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        product_names = [row[0] for row in rows]

        return Response(product_names, status=status.HTTP_200_OK)
        
        
class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow unauthorized access

    @method_decorator(csrf_exempt)
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Hash the password before checking it against the database
        #hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, Employee.empl_role "
                "FROM User_Table "
                "INNER JOIN Employee ON Employee.id_employee = User_Table.id_employee "
                "WHERE username = %s AND user_password = %s",
                [username, password]
            )
            user = cursor.fetchone()
        
        if user:
            user_id, username, role = user
            simple_user = SimpleNamespace(
                id=user_id,
                username=username,
                role=role,
                is_authenticated=True
            )
            refresh = RefreshToken.for_user(simple_user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user_id,
                    'username': username,
                    'role': role,
                }
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CashierView(APIView):
    permission_classes = [IsCashier]

    def get(self, request):
        return Response({'message': 'Hello, Cashier!'})

class ManagerView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        return Response({'message': 'Hello, Manager!'})
    
class TestTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info("TestTokenView accessed with token: %s", request.auth)
        return Response({'message': 'Token is valid'}, status=status.HTTP_200_OK)
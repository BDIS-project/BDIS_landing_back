from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import hashlib

from .permissions import IsCashier, IsManager

class StoreProductsAPIView(APIView):
    """
    API view to retrieve store products using raw SQL.
    """
    permission_classes = [AllowAny]
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

        sorter = "product_name"
        if sort_by:
            if sort_by == 'products-desc':
                sorter = "product_name DESC"
            elif sort_by == 'products-asc':
                sorter = "product_name"
            elif sort_by == 'price-desc':
                sorter = "selling_price DESC"
            elif sort_by == 'price-asc':
                sorter = "selling_price"
            elif sort_by == 'numbers-desc':
                sorter = "products_number DESC"
            else:
                sorter = "products_number"
           
        base_query = (
            "SELECT Store_Product.*, product_name, category_name "
            "FROM Store_Product "
            "INNER JOIN Product ON Store_Product.id_product = Product.id_product "
            "INNER JOIN Category ON Product.category_number = Category.category_number "
            "WHERE 1=1 "
        )


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

        query = base_query + ' '.join(query_conditions) + f" ORDER BY {sorter};"

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
    """
    API view to retrieve all categories using raw SQL.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query = "SELECT category_name FROM Category ORDER BY category_name;"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            categories = cursor.fetchall()
            category_names = [col[0] for col in cursor.description]

        result = [dict(zip(category_names, category)) for category in categories]

        return Response(result, status=status.HTTP_200_OK) 


class ProductsAPIView(APIView):
    """
    API view to retrive products using raw sql
    """
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        query = ("SELECT Product.*, category_name "
                "FROM Product INNER JOIN Category ON Product.category_number = Category.category_number "
                "ORDER BY product_name;")
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            products = cursor.fetchall()
            products_names = [col[0] for col in cursor.description]

        result = [dict(zip(products_names, product)) for product in products]

        return Response(result, status=status.HTTP_200_OK)


class StoreOverviewAPIView(APIView):
    """
    API view to look over store using raw SQL for Manager.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        employee = request.GET.get('employee')
        role = request.GET.get('role')
        employee_surname = request.GET.get('employee-surname')
        customer = request.GET.get('customer')
        percent = request.GET.get('percent')
        categories = request.GET.get('categories')
        category = request.GET.get('category')
        products = request.GET.get('products')
        store_products = request.GET.get('store-products')
        sort_by = request.GET.get('sort-by')
        promotional = request.GET.get('promotional')
        non_promotional = request.GET.get('non-promotional')
        upc = request.GET.get('upc')

        sorter = "product_name"
        if sort_by:
            if sort_by == 'products-desc':
                sorter = "product_name DESC"
            elif sort_by == 'products-asc':
                sorter = "product_name"
            elif sort_by == 'price-desc':
                sorter = "selling_price DESC"
            elif sort_by == 'price-asc':
                sorter = "selling_price"
            elif sort_by == 'numbers-desc':
                sorter = "products_number DESC"
            else:
                sorter = "products_number"

        query = []
        params = []

        if employee is not None:
            query = ["SELECT * FROM Employee"] # Get all employees sorted by surname
            if role:
                query.append("WHERE empl_role = %s") # Get all cashiers sorted by surname
                params.append(role)
            query.append("ORDER BY empl_surname;")
        elif employee_surname: # Get employee address and phone number by surname
            query = [
                "SELECT city, street, phone_number ",
                "FROM Employee ",
                "WHERE empl_surname = %s"
            ]
            params.append(employee_surname)
        elif customer is not None: # Get all regular customers 
            query = ["SELECT * FROM Customer_Card"]
            if percent:
                query.append("WHERE percent = %s")
                params.append(percent)
            query.append("ORDER BY cust_surname;")
        elif categories is not None:
            query = ["SELECT * FROM Category ORDER BY category_name;"]
        elif products is not None:
            query = [
                "SELECT Product.*, category_name ",
                "FROM Product INNER JOIN Category ON Product.category_number = Category.category_number "
            ]
            if category:
                query.append("WHERE category_name = %s ")
                params.append(category)
        elif store_products is not None:
            query = [
                "SELECT Store_Product.*, product_name, category_name ",
                "FROM Store_Product ",
                "INNER JOIN Product ON Store_Product.id_product = Product.id_product ",
                "INNER JOIN Category ON Product.category_number = Category.category_number "
            ]
            if promotional:
                query.append("WHERE promotional_product = TRUE")
            elif non_promotional:
                query.append("WHERE promotional_product = FALSE")
            if sort_by:
                query.append(f"ORDER BY {sorter};")
            else:
                query.append("ORDER BY product_name")
        elif upc:
            query = [
                "SELECT product_name, selling_price, products_number, characteristics ",
                "FROM Store_Product ",
                "INNER JOIN Product ON Store_Product.id_product = Product.id_product ",
                "WHERE upc = %s;"
            ]
            params.append(upc)

        if not query:
            return Response({"error": "No query to execute"}, status=status.HTTP_400_BAD_REQUEST)

        final_query = " ".join(query)

        with connection.cursor() as cursor:
            cursor.execute(final_query, params)
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


class LoginView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Hash the password before checking it against the database
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, role FROM Users WHERE username = %s AND password = %s",
                [username, hashed_password]
            )
            user = cursor.fetchone()
        
        if user:
            user_id, username, role = user
            refresh = RefreshToken.for_user(user)
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
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CashierView(APIView):
    permission_classes = [IsAuthenticated, IsCashier]

    def get(self, request):
        return Response({'message': 'Hello, Cashier!'})


class ManagerView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        return Response({'message': 'Hello, Manager!'})
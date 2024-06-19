from django.db import connection, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import hashlib

from .permissions import IsCashier, IsManager

# adding edit functionality to the data base
# tables: Category, Product, Store_Product, Employee, User_Table, Customer_Card, Check_Table, Sale
# done:   Category, Product, Store_Product, 


class ManagerStoreOverviewAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        view_check = request.GET.get('view_check')
        with_details = request.GET.get('with_details')
        cashier_id = request.GET.get('cashier_id') 
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        all_cashiers = request.GET.get('all_cashiers')
        
        query_conditions = []
        params = []

        base_query = "SELECT * FROM Check_Table WHERE 1=1"

        if view_check:
            query_conditions.append(" AND check_number = %s")
            params.append(view_check)
        if with_details:
            query = "SELECT Product.id_product, product_name, UPC, Sale.selling_price, Sale.product_number FROM ((Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number) INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC) INNER JOIN Product ON Store_Product.id_product = Product.id_product WHERE Check_Table.check_number = %s;"
            params.append(view_check)

        elif cashier_id:
            query_conditions.append(" AND id_employee = %s")
            params.append(cashier_id)
        elif start_date and end_date:
            query_conditions.append(" AND print_date BETWEEN %s AND %s")
            params.append(start_date)
            params.append(end_date)
        elif start_date:
            query_conditions.append(" AND print_date >= %s AND print_date <= NOW()")
            params.append(start_date)
        elif end_date:
            query_conditions.append(" AND print_date >= %s AND print_date <= NOW()")
            params.append(end_date)

        if not with_details:
            query = base_query + ' '.join(query_conditions) + " ORDER BY print_date;"
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            customers = cursor.fetchall()
            last_name = [col[0] for col in cursor.description]

        result = [dict(zip(last_name, customer)) for customer in customers]

        return Response(result, status=status.HTTP_200_OK) 


class CustomerCardOverviewAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        all_clints = request.GET.get('all_clints')
        last_name = request.GET.get('last_name')
        
        query_conditions = []
        params = []

        base_query = "SELECT * FROM Customer_Card WHERE 1=1"
        if last_name:
            query_conditions.append(" AND cust_surname = %s")
            params.append(last_name)

        query = base_query + ' '.join(query_conditions) + " ORDER BY cust_surname;"
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            customers = cursor.fetchall()
            last_name = [col[0] for col in cursor.description]

        result = [dict(zip(last_name, customer)) for customer in customers]

        return Response(result, status=status.HTTP_200_OK) 
    

class CheckOverviewAPIView(APIView):
    
    permission_classes = [IsCashier, IsManager]

    def get(self, request, *args, **kwargs):
        last_day = request.GET.get('last_day')
        complete_check_info = request.GET.get('complete_check_info')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        query_conditions = []
        params = []

        base_query = "SELECT * FROM Check_Table"

        if complete_check_info:
            parts = [
                'SELECT Sale.UPC, Store_Product.id_product, Product.product_name, Store_Product.selling_price, Sale.selling_price AS selling_price_at_sale, Sale.product_number ',
                'FROM Sale INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC INNER JOIN Product ON Store_Product.id_product = Product.id_product ',
                'WHERE Sale.check_number = %s '
            ]
            base_query = "".join(parts)   
            params.append(complete_check_info)

        elif last_day:
            base_query = "SELECT * FROM Check_Table WHERE print_date BETWEEN CURRENT_DATE - INTERVAL '1 day' AND CURRENT_DATE"
            params.append(last_day)    

        elif start_date and end_date:
            base_query = "SELECT * FROM Check_Table WHERE print_date BETWEEN %s AND %s"
            params.append(start_date)
            params.append(end_date)

        elif start_date:     
            base_query = "SELECT * FROM Check_Table WHERE print_date >= %s AND print_date <= NOW()"
            params.append(start_date)

        elif end_date:
            base_query = "SELECT * FROM Check_Table WHERE print_date <= %s AND print_date >= NOW()"
            params.append(end_date)

        query = base_query + ';'
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            checks = cursor.fetchall()
            check_number = [col[0] for col in cursor.description]

        result = [dict(zip(check_number, check)) for check in checks]

        return Response(result, status=status.HTTP_200_OK) 
    

class StoreProductsAPIView(APIView):
    """
    API view to retrieve store products using raw SQL.
    """
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        upc = request.GET.get('UPC')
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
    
    def post(self, request, *args, **kwargs):
        UPC = request.data.get('UPC')
        UPC_prom = request.data.get('UPC_prom')
        id_product = request.data.get('id_product')
        selling_price = request.data.get('selling_price')
        products_number = request.data.get('products_number')
        expire_date = request.data.get('expire_date')
        promotional_product = request.data.get('promotional_product')

        if not UPC or not id_product or not selling_price or not products_number or not expire_date or promotional_product is None:
            return Response({"error": "UPC, id_product, selling_price, products_number, expire_date, and promotional_product are required"}, status=status.HTTP_400_BAD_REQUEST)

        cursor = connection.cursor()

        set_values = []
        params = []

        if UPC_prom is not None:
            set_values.append("UPC_prom = %s")
            params.append(UPC_prom)
        if id_product is not None:
            set_values.append("id_product = %s")
            params.append(id_product)
        if selling_price is not None:
            set_values.append("selling_price = %s")
            params.append(selling_price)
        if products_number is not None:
            set_values.append("products_number = %s")
            params.append(products_number)
        if expire_date is not None:
            set_values.append("expire_date = %s")
            params.append(expire_date)
        if promotional_product is not None:
            set_values.append("promotional_product = %s")
            params.append(promotional_product)

        query = f"""
            UPDATE Store_Product
            SET {', '.join(set_values)}
            WHERE UPC = %s
            RETURNING UPC;
        """
        params.append(UPC)

        cursor.execute(query, params)
        updated_UPC = cursor.fetchone()[0]
        connection.commit()

        return Response({"UPC": updated_UPC, "message": "Store Product updated successfully"}, status=status.HTTP_200_OK)


class CategoriesAPIView(APIView):
    """
    API view to retrieve, update all categories using raw SQL.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query = "SELECT * FROM Category ORDER BY category_name;"

        with connection.cursor() as cursor:
            cursor.execute(query)
            categories = cursor.fetchall()
            category_names = [col[0] for col in cursor.description]

        result = [dict(zip(category_names, category)) for category in categories]

        return Response(result, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        category_number = kwargs.get('category_number')
        category_name = request.data.get('category_name')

        if not category_number or not category_name:
            return Response({"error": "Category number and category_name are required"}, status=status.HTTP_400_BAD_REQUEST)

        cursor = connection.cursor()

        query = "UPDATE Category SET category_name = %s WHERE category_number = %s;"
        cursor.execute(query, (category_name, category_number))
        connection.commit()

        return Response({"message": "Category updated successfully"}, status=status.HTTP_200_OK)


class ProductsAPIView(APIView):
    """
    API view to retrive, update products using raw sql
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
    
    def post(self, request, *args, **kwargs):
        id_product = request.data.get('id_product')
        category_number = request.data.get('category_number')
        product_name = request.data.get('product_name')
        characteristics = request.data.get('characteristics')
        picture = request.data.get('picture')

        if not id_product or (not category_number and not product_name and not characteristics and not picture):
            return Response({"error": "At least one field (category_number, product_name, characteristics, picture) is required"}, status=status.HTTP_400_BAD_REQUEST)

        cursor = connection.cursor()

        set_values = []
        params = []

        if category_number is not None:
            set_values.append("category_number = %s")
            params.append(category_number)
        if product_name is not None:
            set_values.append("product_name = %s")
            params.append(product_name)
        if characteristics is not None:
            set_values.append("characteristics = %s")
            params.append(characteristics)
        if picture is not None:
            set_values.append("picture = %s")
            params.append(picture)

        query = f"""
            UPDATE Product
            SET {', '.join(set_values)}
            WHERE id_product = %s
            RETURNING id_product;
        """
        params.append(id_product)

        cursor.execute(query, params)
        updated_id_product = cursor.fetchone()[0]
        connection.commit()

        return Response({"id_product": updated_id_product, "message": "Product updated successfully"}, status=status.HTTP_200_OK)


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
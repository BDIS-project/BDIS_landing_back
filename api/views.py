from django.db import connection, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from types import SimpleNamespace

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import hashlib
import logging

import random
import string
import json
from decimal import Decimal

from api.permissions import (
    IsAuthenticated,
    AllowAny,
    IsCashier, 
    IsManager, 
    IsCashierOrManager 
)
from api.auth import JWTAuthentication
from api.processing import process_store_products
logger = logging.getLogger(__name__)

# adding edit functionality to the data base
# tables: Category, Product, Store_Product, Employee, Customer_Card, Check_Table, Sale
# done:   Category, Product, Store_Product, 

class ProductsAPIView(APIView):
    """
    API view to retrive, update products using raw sql FOR CASHIER
    """
    permission_classes = [IsCashierOrManager]
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
    

class StoreProductsAPIView(APIView):
    """
    API view to retrieve store products using raw SQL for CASHIER
    Currently used as homepage
    """
    permission_classes = [IsCashierOrManager]
    def get(self, request, *args, **kwargs):
        process_store_products()

        search = request.GET.get('search')
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
            "SELECT Store_Product.*, product_name, category_name, picture "
            "FROM Store_Product "
            "INNER JOIN Product ON Store_Product.id_product = Product.id_product "
            "INNER JOIN Category ON Product.category_number = Category.category_number "
            "WHERE 1=1 "
        )

        if search:
            # Check for product name match first
            product_name_query = (
                "SELECT COUNT(*) FROM Product WHERE product_name LIKE %s"
            )
            with connection.cursor() as cursor:
                cursor.execute(product_name_query, ['%' + search + '%'])
                product_name_count = cursor.fetchone()[0]

            if product_name_count > 0:
                query_conditions.append("AND product_name LIKE %s")
                params.append('%' + search + '%')
            else:
                query_conditions.append("AND UPC = %s")
                params.append(search)

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
            query_conditions.append(f"AND Category.category_number IN ({','.join(['%s'] * len(category_list))})")
            params.extend(category_list)
        if in_stock:
            if in_stock.lower() == 'true':
                query_conditions.append("AND products_number > 0")

        
        query = base_query + ' '.join(query_conditions) + f" ORDER BY (products_number = 0), {sorter};"

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
    

class OnlyStoreProductsAPIView(APIView):
    """
    API view to retrieve all info about store products
    and store products only, for MANAGER and CASHIER
    """
    permission_classes = [IsCashierOrManager]
    def get(self, request, *args, **kwargs):
        query = "SELECT * FROM Store_Product;"

        with connection.cursor() as cursor:
            cursor.execute(query)
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

class CheckOverviewAPIView(APIView):
    """
    API view to retrieve store products using raw SQL for CASHIER
    """
    
    permission_classes = [IsCashierOrManager]

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


class CategoriesAPIView(APIView):
    """
    API view to retrieve, update all categories using raw SQL 
    for MANAGER and CreateProductAPIView DROPDOWN LIST
    """
    permission_classes = [IsCashierOrManager]

    def get(self, request, *args, **kwargs):

        query = "SELECT category_number, category_name FROM Category ORDER BY category_name;"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            categories = cursor.fetchall()
            category_names = [col[0] for col in cursor.description]

        result = [dict(zip(category_names, category)) for category in categories]

        return Response(result, status=status.HTTP_200_OK)
    

class ProductNamesAPIView(APIView):
    """
    API view to retrive Products names and pk DROPDOWN LIST for MANAGER
    """
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        query = "SELECT id_product, product_name FROM Product ORDER BY product_name;"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            products = cursor.fetchall()
            product_names = [col[0] for col in cursor.description]

        result = [dict(zip(product_names, product)) for product in products]

        return Response(result, status=status.HTTP_200_OK)
    

class StoreOverviewAPIView(APIView):
    """
    API view to look over store using raw SQL for MANAGER.
    """
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        process_store_products()
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
    

class AboutMeAPIView(APIView):
    """
    API view to rethrive all info about CASHIER
    currently loggen in
    """
    permission_classes = [IsCashier]
    def get(self, request, *args, **kwargs):
        user_id = request.user["id"]
        with connection.cursor() as cursor:
            cursor.execute(
            "SELECT id_employee "
            "FROM User_Table "
            "WHERE user_id = %s",
            [user_id])

            cashier_id = cursor.fetchone()
        
        employee_query = """SELECT * FROM EMPLOYEE
        WHERE id_employee = %s;
        """
        check_query = """ SELECT * FROM Check_Table
        WHERE id_employee = %s;
        """
        params = [cashier_id]

        with connection.cursor() as cursor:
            cursor.execute(employee_query, params)
            employee = cursor.fetchall()
            employee_names = [col[0] for col in cursor.description]

        employee_result = [dict(zip(employee_names, empl)) for empl in employee]

        with connection.cursor() as cursor:
            cursor.execute(check_query, params)
            checks = cursor.fetchall()
            checks_names = [col[0] for col in cursor.description]

        checks_results = [dict(zip(checks_names, check)) for check in checks]

        result = {
            'employee': employee_result,
            'checks': checks_results
        }

        return Response(result, status=status.HTTP_200_OK)


class CustomerCardOverviewAPIView(APIView):
    permission_classes = [IsCashierOrManager]

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
    

# Why store overview when its only about checks?
class ManagerStoreOverviewAPIView(APIView):
    permission_classes = [IsManager]

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


class CompleteSingleCheckOverviewAPIView(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        check_number = request.GET.get('check_number')
        with_details = request.GET.get('with_details')
        cashier_id = request.GET.get('cashier_id') 
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        query_conditions = []
        params = []

        base_query = "SELECT * FROM Check_Table WHERE 1=1"
        query = ''

        if with_details and check_number:
            # Product.id_product, product_name, Sale.UPC, Sale.selling_price, Sale.product_number 
            query = """
            SELECT Product.id_product, product_name, Sale.UPC, Sale.selling_price, Sale.product_number 
            FROM ((Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number) 
                INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC) 
                INNER JOIN Product ON Store_Product.id_product = Product.id_product
            WHERE Check_Table.check_number = %s;
            """
            params.append(check_number)
        elif check_number:
            query_conditions.append(" AND check_number = %s")
            params.append(check_number)
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

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                customers = cursor.fetchall()
                last_name = [col[0] for col in cursor.description]

            result = [dict(zip(last_name, customer)) for customer in customers]
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CompleteEveryChecksOverviewAPIView(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        check_number = request.GET.get('check_number')
        with_details = request.GET.get('with_details')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        query_conditions = []
        params = []

        base_query = "SELECT * FROM Check_Table WHERE 1=1"
        query = ''

        if with_details and check_number:
            query = """
            SELECT Product.id_product, product_name, Sale.UPC, Sale.selling_price, Sale.product_number 
            FROM ((Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number) 
                INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC) 
                INNER JOIN Product ON Store_Product.id_product = Product.id_product
            WHERE Check_Table.check_number = %s;
            """
            params.append(check_number)
        elif check_number:
            query_conditions.append(" AND check_number = %s")
            params.append(check_number)
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

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                customers = cursor.fetchall()
                last_name = [col[0] for col in cursor.description]

            result = [dict(zip(last_name, customer)) for customer in customers]
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductsSoldByACashierCount(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        cashier_id = request.GET.get('cashier_id') 
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        query_conditions = []
        params = []

        base_query = """
            SELECT COALESCE(SUM(subquery.total_sum), 0) AS overall_total_sum
            FROM (
                SELECT SUM(Sale.product_number) AS total_sum
                FROM Check_Table
                    INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
                    INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
                    INNER JOIN Product ON Store_Product.id_product = Product.id_product
                WHERE 1=1
            """
        
        if not cashier_id:
            return Response({'error': 'Parameter cashier_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if cashier_id:
            query_conditions.append(" AND id_employee = %s")
            params.append(cashier_id)
        
        if start_date and end_date:
            query_conditions.append(" AND print_date BETWEEN %s AND %s")
            params.append(start_date)
            params.append(end_date)
        elif start_date:
            query_conditions.append(" AND print_date >= %s")
            params.append(start_date)
        elif end_date:
            query_conditions.append(" AND print_date <= %s")
            params.append(end_date)

        query = base_query + ' '.join(query_conditions) + """
                GROUP BY Check_Table.check_number
            ) AS subquery;
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductsSoldByAllCashiersCount(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        query_conditions = []
        params = []

        base_query = """
            SELECT COALESCE(SUM(subquery.total_sum), 0) AS overall_total_sum
            FROM (
                SELECT SUM(Sale.product_number) AS total_sum
                FROM Check_Table
                    INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
                    INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
                    INNER JOIN Product ON Store_Product.id_product = Product.id_product
                WHERE 1=1
            """
        
        if start_date and end_date:
            query_conditions.append(" AND print_date BETWEEN %s AND %s")
            params.append(start_date)
            params.append(end_date)
        elif start_date:
            query_conditions.append(" AND print_date >= %s")
            params.append(start_date)
        elif end_date:
            query_conditions.append(" AND print_date <= %s")
            params.append(end_date)

        query = base_query + ' '.join(query_conditions) + """
                GROUP BY Check_Table.check_number
            ) AS subquery;
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductSoldCountAPIView(APIView): # maybe need to change use UPC insted of id_product
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        product_id = request.GET.get('product_id') 
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        query_conditions = []
        params = []

        base_query = """
            SELECT COALESCE(SUM(Sale.product_number), 0) AS total_quantity_sold
            FROM Check_Table
                INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
                INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
                INNER JOIN Product ON Store_Product.id_product = Product.id_product
            WHERE 1=1
            """
        
        if not product_id:
            return Response({'error': 'Parameter product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if product_id:
            query_conditions.append(" AND Product.id_product = %s")
            params.append(product_id)
        
        if start_date and end_date:
            query_conditions.append(" AND print_date BETWEEN %s AND %s")
            params.append(start_date)
            params.append(end_date)
        elif start_date:
            query_conditions.append(" AND print_date >= %s")
            params.append(start_date)
        elif end_date:
            query_conditions.append(" AND print_date <= %s")
            params.append(end_date)

        query = base_query + ' '.join(query_conditions) + ";"

    
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                products = cursor.fetchall()
                product_id = [col[0] for col in cursor.description]

            result = [dict(zip(product_id, product)) for product in products]
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class CreateCategoryAPIView(APIView):
    """
    API view to create Categories for MANAGER
    """
    permission_classes = [IsManager]
    def post(self, request, *args, **kwargs):
        category_name = request.data.get('category-name')

        # check if all neccesary parameters are present
        if not category_name:
            return Response({'error': 'Category name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        query = "INSERT INTO Category (category_name) VALUES (%s);"
        vals = [category_name]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Category created successfully'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': 'Category could not be created'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateProductAPIView(APIView):
    """
    API view to create Products for MANAGER
    """
    permission_classes = [IsManager]
    def post(self, request, *args, **kwargs):
        category_number = request.data.get('category-number')
        product_name = request.data.get('name')
        characteristics = request.data.get('characteristics')
        picture = request.data.get('picture', None)

        # check if all neccesary parameters are present
        if not category_number or not product_name or not characteristics:
            return Response({'error': 'Required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)

        query = """
        INSERT INTO Product (category_number, product_name, characteristics, picture)
        VALUES (%s, %s, %s, %s);
        """
        vals = [category_number, product_name, characteristics, picture]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Product created successfully'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': 'Product could not be created due to integrity error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
class CreateStoreProductAPIView(APIView):
    """
    API view to create Store Products for MANAGER
    """
    permission_classes = [IsManager]

    def post(self, request, *args, **kwargs):
        UPC = request.data.get('UPC')
        UPC_prom = None
        id_product = request.data.get('id')
        selling_price = request.data.get('price')
        products_number = request.data.get('products-number')
        expire_date = request.data.get('expire-date')
        promotional_product = False

        # check if all neccesary parameters are present
        if not all([UPC, id_product, selling_price, products_number, expire_date, promotional_product is not None]):
            return Response({'error': 'Required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        query = """
        INSERT INTO Store_Product (UPC, UPC_prom, id_product, selling_price, products_number, expire_date, promotional_product)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        vals = [UPC, UPC_prom, id_product, selling_price, products_number, expire_date, promotional_product]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
                process_store_products()
            return Response({'message': 'Store Product created successfully'}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({'error': 'Store Product could not be created due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateEmployeeAPIView(APIView):
    """
    API view to create Employee for MANAGER
    """
    permission_classes = [IsManager]
    def post(self, request, *args, **kwargs):
        id_employee = request.data.get('id')
        empl_surname = request.data.get('surname')
        empl_name = request.data.get('name')
        empl_patronymic = request.data.get('patronymic')
        empl_role = request.data.get('role')
        salary = request.data.get('salary')
        date_of_birth = request.data.get('birth')
        date_of_start = request.data.get('start')
        phone_number = request.data.get('phone')
        city = request.data.get('city', None)
        street = request.data.get('street', None)
        zip_code = request.data.get('zip-code', None)

        # check if all neccesary parameters are present
        if (not id_employee or not empl_surname or not empl_name or not empl_patronymic or not empl_role 
        or not salary or not date_of_birth or not date_of_start or not phone_number or not city or not street or not zip_code):
            return Response({'error': 'Required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)

        
        query = """
        INSERT INTO Employee (id_employee, empl_surname, empl_name, empl_patronymic, empl_role, salary, date_of_birth, 
        date_of_start, phone_number, city, street, zip_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        vals = [id_employee, empl_surname, empl_name, empl_patronymic, empl_role, salary, 
                date_of_birth, date_of_start, phone_number, city, street, zip_code]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Employee created successfully'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': 'Employee could not be created'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CreateCustomerAPIView(APIView):
    """
    API view to create Customer Card for MANAGER and CASHIER
    """
    permission_classes = [IsCashierOrManager]
    def post(self, request, *args, **kwargs):
        card_number = request.data.get('card-number')
        cust_surname = request.data.get('surname')
        cust_name = request.data.get('name')
        cust_patronymic = request.data.get('patronymic')
        phone_number = request.data.get('phone')
        city = request.data.get('city', None)
        street = request.data.get('street', None)
        zip_code = request.data.get('zip-code', None)
        percent = request.data.get('percent')

        # check if all neccesary parameters are present
        if not card_number or not cust_surname or not cust_name or not phone_number or not percent:
            return Response({'error': 'Required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        query = """
        INSERT INTO Customer_Card (card_number, cust_surname, cust_name, cust_patronymic, phone_number, city,
          street, zip_code, percent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        

        vals = [card_number, cust_surname, cust_name, cust_patronymic, phone_number, city, street, zip_code, percent]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Customer Card created successfully'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': 'Customer Card could not be created'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustumerPercentAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        API view to retrive info about customers
        and their percents
        """

        query = """
        SELECT card_number, cust_surname, percent
        FROM Customer_Card
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)


class CreateCheckAPIView(APIView):
    permission_classes = [IsCashier]
    def post(self, request, *args, **kwargs):
        client_id = request.data.get('client')
        sold_products = request.data.get('sold_products')

        # Check if all necessary parameters are present
        if not sold_products:
            return Response({'error': 'Required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the amount is not more than products_number
        for product in sold_products:
            upc = product.get('upc')
            amount = product.get('amount')
            with connection.cursor() as cursor:
                cursor.execute("SELECT products_number FROM Store_Product WHERE UPC = %s", [upc])
                result = cursor.fetchone()
                if not result or result[0] < amount:
                    return Response({'error': f'Not enough products in stock for UPC {upc}'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique check number
        def generate_unique_check_number():
            while True:
                check_number = ''.join(random.choices(string.digits, k=10))
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM Check_Table WHERE check_number = %s", [check_number])
                    if cursor.fetchone()[0] == 0:
                        return check_number

        check_number = generate_unique_check_number()
        
        sum_total = Decimal('0.0')
        try:
            # Calculate sum_total
            for product in sold_products:
                upc = product.get('upc')
                amount = product.get('amount')

                # Get selling price
                with connection.cursor() as cursor:
                    cursor.execute("SELECT selling_price FROM Store_Product WHERE UPC = %s", [upc])
                    selling_price = cursor.fetchone()[0]
                    cursor.execute("UPDATE Store_Product SET products_number = products_number - %s WHERE UPC = %s", [amount, upc])

                sum_total += Decimal(str(selling_price)) * Decimal(str(amount))

            # Calculate total sum and VAT
            vat = sum_total * Decimal('0.2')
            sum_total = sum_total + vat


            # Get discount percentage if client ID is provided
            discount_percent = Decimal('0.0')
            if client_id:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT percent FROM Customer_Card WHERE card_number = %s",
                        [client_id]
                    )
                    result = cursor.fetchone()
                    if result:
                        discount_percent = Decimal(str(result[0])) / Decimal('100.0')
            else:
                client_id = None

            sum_total = sum_total - (sum_total * discount_percent)

            user_id = request.user["id"]
            with connection.cursor() as cursor:
                cursor.execute(
                "SELECT id_employee "
                "FROM User_Table "
                "WHERE user_id = %s",
                [user_id])

                cashier_id = cursor.fetchone()
              

            # Insert into Check_Table
            with connection.cursor() as cursor:
                if cashier_id:
                    cursor.execute(
                    """
                    INSERT INTO Check_Table (check_number, id_employee, card_number, print_date, sum_total)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    [check_number, cashier_id, client_id, sum_total]
                    )
                else:
                    cursor.execute(
                    """
                    INSERT INTO Check_Table (check_number, id_employee, print_date, sum_total)
                    VALUES (%s, %s, NOW(), %s)
                    """,
                    [check_number, cashier_id, sum_total]
                    )


            # Insert sales
            for product in sold_products:
                upc = product.get('upc')
                amount = product.get('amount')

                # Get selling price
                with connection.cursor() as cursor:
                    cursor.execute("SELECT selling_price FROM Store_Product WHERE UPC = %s", [upc])
                    selling_price = cursor.fetchone()[0]

                # Insert into Sale table
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO Sale (UPC, check_number, product_number, selling_price) VALUES (%s, %s, %s, %s)",
                        [upc, check_number, amount, selling_price]
                    )

            return Response({'message': 'Check created successfully', 'check_number': check_number}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            return Response({'error': 'Could not create check due to integrity error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Update_CategoriesAPIView(APIView):
    permission_classes = [IsManager]

    def post(self, request, category_number, *args, **kwargs):
        category_name = request.data.get('category_name')

        if not category_name:
            return Response({"error": "Category number and category_name are required"}, status=status.HTTP_400_BAD_REQUEST)

        cursor = connection.cursor()

        query = "UPDATE Category SET category_name = %s WHERE category_number = %s;"
        cursor.execute(query, [category_name, category_number])
        connection.commit()

        return Response({"message": "Category updated successfully"}, status=status.HTTP_200_OK)
    

class Update_ProductsAPIView(APIView):
    permission_classes = [IsManager]

    def post(self, request, id_product, *args, **kwargs):
        category_number = request.data.get('category_number')
        product_name = request.data.get('product_name')
        characteristics = request.data.get('characteristics')
        picture = request.data.get('picture')

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

        if not set_values:
            return Response({"error": "At least one of category_number, product_name, characteristics, picture is required"}, status=status.HTTP_400_BAD_REQUEST)

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


class Update_StoreProductsAPIView(APIView):
    permission_classes = [IsCashierOrManager]

    def post(self, request, *args, **kwargs):
        # Extract all possible fields that can be updated
        upc = request.data.get('upc')
        id_product = request.data.get('id_product')
        selling_price = request.data.get('selling_price')
        products_number = request.data.get('products_number')
        expire_date = request.data.get('expire_date')

        cursor = connection.cursor()

        # Build the SET clause dynamically based on provided fields
        set_values = []
        params = []

        if upc is not None:
            set_values.append("UPC = %s")
            params.append(upc)
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
        

        # Check current promotional status for the given UPC
        query = """
            SELECT id_product, promotional_product
            FROM Store_Product
            WHERE UPC = %s;
        """
        cursor.execute(query, [upc])
        row = cursor.fetchone()

        if not row:
            return Response({"error": "Store Product not found"}, status=status.HTTP_404_NOT_FOUND)

        id_product, current_promotional = row
       
        # No change in promotional status, only update specified attributes
        set_clause = ', '.join(set_values)
        query = f"""
            UPDATE Store_Product
            SET {set_clause}
            WHERE UPC = %s;
        """
        params.append(upc)
        cursor.execute(query, params)
        connection.commit()

        return Response({"message": "Store Product updated successfully"}, status=status.HTTP_200_OK)
        

class Update_EmployeeAPIView(APIView):
    permission_classes = [IsManager]

    def post(self, request, id_employee, *args, **kwargs):
        # Extract all possible fields that can be updated
        empl_surname = request.data.get('empl_surname')
        empl_name = request.data.get('empl_name')
        empl_patronymic = request.data.get('empl_patronymic')
        empl_role = request.data.get('empl_role')
        salary = request.data.get('salary')
        date_of_birth = request.data.get('date_of_birth')
        date_of_start = request.data.get('date_of_start')
        phone_number = request.data.get('phone_number')
        city = request.data.get('city')
        street = request.data.get('street')
        zip_code = request.data.get('zip_code')

        cursor = connection.cursor()

        # Build the SET clause dynamically based on provided fields
        set_values = []
        params = []

        if empl_surname is not None:
            set_values.append("empl_surname = %s")
            params.append(empl_surname)
        if empl_name is not None:
            set_values.append("empl_name = %s")
            params.append(empl_name)
        if empl_patronymic is not None:
            set_values.append("empl_patronymic = %s")
            params.append(empl_patronymic)
        if empl_role is not None:
            set_values.append("empl_role = %s")
            params.append(empl_role)
        if salary is not None:
            set_values.append("salary = %s")
            params.append(salary)
        if date_of_birth is not None:
            set_values.append("date_of_birth = %s")
            params.append(date_of_birth)
        if date_of_start is not None:
            set_values.append("date_of_start = %s")
            params.append(date_of_start)
        if phone_number is not None:
            set_values.append("phone_number = %s")
            params.append(phone_number)
        if city is not None:
            set_values.append("city = %s")
            params.append(city)
        if street is not None:
            set_values.append("street = %s")
            params.append(street)
        if zip_code is not None:
            set_values.append("zip_code = %s")
            params.append(zip_code)

        # If no fields to update are provided, return an error response
        if not set_values:
            return Response({"error": "At least one attribute (empl_surname, empl_name, empl_patronymic, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code) is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update all specified attributes
            set_clause = ', '.join(set_values)
            query = f"""
                UPDATE Employee
                SET {set_clause}
                WHERE id_employee = %s;
            """
            params.append(id_employee)
            cursor.execute(query, params)
            connection.commit()

            return Response({"message": "Employee information updated successfully"}, status=status.HTTP_200_OK)

        except IntegrityError as e:
            connection.rollback()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)  
        

class Update_CustomerCardView(APIView):
    permission_classes = [IsManager]

    def post(self, request, card_number, *args, **kwargs):
        # Extract all possible fields that can be updated
        cust_surname = request.data.get('cust_surname')
        cust_name = request.data.get('cust_name')
        cust_patronymic = request.data.get('cust_patronymic')
        phone_number = request.data.get('phone_number')
        city = request.data.get('city')
        street = request.data.get('street')
        zip_code = request.data.get('zip_code')
        percent = request.data.get('percent')

        cursor = connection.cursor()

        # Build the SET clause dynamically based on provided fields
        set_values = []
        params = []

        if cust_surname is not None:
            set_values.append("cust_surname = %s")
            params.append(cust_surname)
        if cust_name is not None:
            set_values.append("cust_name = %s")
            params.append(cust_name)
        if cust_patronymic is not None:
            set_values.append("cust_patronymic = %s")
            params.append(cust_patronymic)
        if phone_number is not None:
            set_values.append("phone_number = %s")
            params.append(phone_number)
        if city is not None:
            set_values.append("city = %s")
            params.append(city)
        if street is not None:
            set_values.append("street = %s")
            params.append(street)
        if zip_code is not None:
            set_values.append("zip_code = %s")
            params.append(zip_code)
        if percent is not None:
            set_values.append("percent = %s")
            params.append(percent)

        # If no fields to update are provided, return an error response
        if not set_values:
            return Response({"error": "At least one attribute (cust_surname, cust_name, cust_patronymic, phone_number, city, street, zip_code, percent) is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update all specified attributes
            set_clause = ', '.join(set_values)
            query = f"""
                UPDATE Customer_Card
                SET {set_clause}
                WHERE card_number = %s;
            """
            params.append(card_number)
            cursor.execute(query, params)
            connection.commit()

            return Response({"message": "Customer card information updated successfully"}, status=status.HTTP_200_OK)

        except IntegrityError as e:
            connection.rollback()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class Update_CheckTableView(APIView):
    permission_classes = [IsManager]

    def post(self, request, check_number, *args, **kwargs):
        id_employee = request.data.get('id_employee')
        card_number = request.data.get('card_number')
        print_date = request.data.get('print_date')
        sum_total = request.data.get('sum_total')

        cursor = connection.cursor()

        # Build the SET clause dynamically based on provided fields
        set_values = []
        params = []

        if id_employee is not None:
            set_values.append("id_employee = %s")
            params.append(id_employee)
        if card_number is not None:
            set_values.append("card_number = %s")
            params.append(card_number)
        if print_date is not None:
            set_values.append("print_date = %s")
            params.append(print_date)
        if sum_total is not None:
            set_values.append("sum_total = %s")
            params.append(sum_total)

        # If no fields to update are provided, return an error response
        if not set_values:
            return Response({"error": "At least one attribute (id_employee, card_number, print_date, sum_total) is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update all specified attributes
            set_clause = ', '.join(set_values)
            query = f"""
                UPDATE Check_Table
                SET {set_clause}
                WHERE check_number = %s;
            """
            params.append(check_number)
            cursor.execute(query, params)
            connection.commit()

            return Response({"message": "Check information updated successfully"}, status=status.HTTP_200_OK)

        except IntegrityError as e:
            connection.rollback()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteCategoryAPIView(APIView):
    """
    API view to delete Category for MANAGER
    """
    permission_classes = [IsManager]

    def delete(self, request, category_number, *args, **kwargs):
        query = "DELETE FROM Category WHERE category_number = %s;"
        vals = [category_number]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Category deleted successfully'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({'error': 'Category could not be deleted due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      

class DeleteProductAPIView(APIView):
    """
    API view to delete Product for MANAGER
    """
    permission_classes = [IsManager]
    def delete(self, request, id_product, *args, **kwargs):
        query = "DELETE FROM Product WHERE id_product = %s;"
        vals = [id_product]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Product deleted successfully'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({'error': 'Product could not be deleted due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteStoreProductAPIView(APIView):
    """
    API view to delete Store Product for MANAGER
    """
    permission_classes = [IsManager]
    def delete(self, request, UPC, *args, **kwargs):
        query = "DELETE FROM Store_Product WHERE UPC = %s;"
        vals = [UPC]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Store Product deleted successfully'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({'error': 'Store Product could not be deleted due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteEmployeeAPIView(APIView):
    """
    API view to delete Employee for MANAGER
    """
    permission_classes = [IsManager]
    def delete(self, request, id_employee, *args, **kwargs):
        query = "DELETE FROM Employee WHERE id_employee = %s;"
        vals = [id_employee]

        # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Employee deleted successfully'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({'error': 'Employee could not be deleted due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteCustomerAPIView(APIView):
    """
    API view to delete Customer Card for MANAGER
    """

    permission_classes = [IsManager]
    def delete(self, request, card_number, *args, **kwargs):
        query = "DELETE FROM Customer_Card WHERE card_number = %s;"
        vals = [card_number]

         # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Customer Card deleted successfully'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({'error': 'Customer Card could not be deleted due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteCheckAPIView(APIView):
    """
    API view to delete Check for MANAGER
    """
    permission_classes = [IsManager]
    def delete(self, request, check_number, *args, **kwargs):
        query = "DELETE FROM Check_Table WHERE check_number = %s;"
        vals = [check_number]

         # return result of query execution
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, vals)
            return Response({'message': 'Check deleted successfully'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({'error': 'Check could not be deleted due to integrity error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class StatisticsAPIView(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        result = self.create_report()

        return Response(result, status=status.HTTP_200_OK)

    def create_report(self, *args, **kwargs):
        json_report_as_string = """
        {
            "report": {

        """

        #create json from Category table
        category_json = self.table_to_json_string("Category")
        product_json = self.table_to_json_string("Product")
        store_product_json = self.table_to_json_string("Store_Product")
        employee_json = self.table_to_json_string("Employee")
        customer_card_json = self.table_to_json_string("Customer_Card")
        check_table_json = self.table_to_json_string("Check_Table")
        sale_json = self.table_to_json_string("Sale")

        json_report_as_string += category_json
        json_report_as_string += product_json
        json_report_as_string += store_product_json
        json_report_as_string += employee_json
        json_report_as_string += customer_card_json
        json_report_as_string += check_table_json
        json_report_as_string += sale_json

        json_report_as_string += """
            }
        }
        """

        return json_report_as_string


    def table_to_json_string(self, table_name, *args, **kwargs):
        query = f"SELECT * FROM {table_name};"

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return json.dumps(rows)

# Evelina
class CategoriesSummaryAPIView(APIView):

    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        """
        API view to retrive info about each category
        total revenue or number of products sold using raw SQL.
        """

        metric = request.GET.get('metric')
        
        if metric == 'quantity':
            aggregation_field  = 'product_number'
            result_label = 'total_units_sold'
        elif metric == 'revenue':
            aggregation_field  = 'Sale.selling_price'
            result_label = 'total_revenue'
        else:
            return Response({"error": "Invalid metric parameter. Use 'quantity' or 'revenue'."}, status=status.HTTP_400_BAD_REQUEST)

        params = [aggregation_field, result_label]

        query = """
        SELECT Category.category_name, SUM({0}) AS {1}
        FROM Sale
        INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
        INNER JOIN Product ON Store_Product.id_product = Product.id_product
        INNER JOIN Category ON Product.category_number = Category.category_number
        GROUP BY Category.category_name;
        """.format(aggregation_field, result_label)

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)
 

# Evelina
class SoldEveryProductAPIView(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        """
        API view to retrive info about employees that 
        sold each product at leans once
        """

        query = """
        SELECT DISTINCT id_employee, empl_surname
        FROM Employee
        WHERE NOT EXISTS (
        SELECT UPC
        FROM Store_Product
        WHERE NOT EXISTS (
        SELECT Sale.check_number
        FROM Sale
        INNER JOIN Check_Table ON Check_Table.check_number = Sale.check_number
        WHERE Employee.id_employee = Check_Table.id_employee AND Store_Product.UPC = Sale.UPC
        )
        );"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)


# Andrii
class CategoryAveragePrice(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        """
        Retrieve the average selling price for each category, 
        optionally excluding promotional products.
        """

        include_promotional = request.GET.get('include_promotional', 'true').lower() in ('true', '1')

        query = """
        SELECT 
            Category.category_number, 
            Category.category_name, 
            COALESCE(ROUND(AVG(Store_Product.selling_price), 2), 0) AS avg_selling_price
        FROM 
            Category 
            LEFT JOIN Product ON Category.category_number = Product.category_number
            LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
        WHERE 1=1
        """

        if not include_promotional:
            query += " AND Store_Product.promotional_product = FALSE"

        query += """
        GROUP BY 
            Category.category_number, Category.category_name
        ORDER BY 
            Category.category_number;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)


# Andrii
class AllProductsAreSold(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        """
        Retrieve categories where all products are being sold.
        """

        query = """
        SELECT Category.category_number,
        Category.category_name
        FROM Category 
        WHERE NOT EXISTS (SELECT Product.id_product
        FROM Product
        WHERE Product.category_number = Category.category_number 
        AND id_product NOT IN (SELECT Store_Product.id_product
        FROM Store_Product
        )
        );"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)


# Damian
class AllCategories(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        """
        API view to retrieve categories 
        which currently have all products in store 
        """

        query = """
        SELECT * 
        FROM Category
        WHERE NOT EXISTS (SELECT *
        FROM Product
        WHERE id_product NOT IN (SELECT id_product
        FROM Store_Product
        ) 
        AND Category.category_number = Product.category_number
        )
        ORDER BY category_number, category_name;"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)


# Damian
class CategoryProductInfo(APIView):
    permission_classes = [IsManager]

    def get(self, request, *args, **kwargs):
        """
        API view to get 
        complete info about categories and all the products
        """

        lower_end_quantity = request.GET.get('lower_end_quantity')

        lower_end_quantity = request.GET.get('lower_end_quantity')

        query = """
        SELECT c.category_number, c.category_name, COALESCE(SUM(products_number),0) AS count
        FROM (Category AS c LEFT JOIN Product ON c.category_number = Product.category_number)
        LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
        GROUP BY c.category_number, c.category_name
        
        """

        if lower_end_quantity is not None:
            query += ' HAVING COALESCE(SUM(store_product.products_number),0)>%s'
        else:
            query += ' ORDER BY c.category_number, c.category_name'
        query += ';'
        
        """

        if lower_end_quantity is not None:
            query += ' HAVING COALESCE(SUM(product_number),0)>%s'
        
        query += ' ORDER BY c.category_number, c.category_name;'

        with connection.cursor() as cursor:
            cursor.execute(query, [lower_end_quantity])
            cursor.execute(query, [lower_end_quantity])
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)"""
    

        
class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow unauthorized access

    @method_decorator(csrf_exempt)
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Hash the password before checking it against the database
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, Employee.empl_role "
                "FROM User_Table "
                "INNER JOIN Employee ON Employee.id_employee = User_Table.id_employee "
                "WHERE username = %s AND user_password = %s",
                [username, hashed_password.lower()]
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
        try:
            refresh_token = request.data.get('refresh_token')

            if not refresh_token:
                return Response({"detail": "No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the refresh token
            JWTAuthentication().blacklist_token(refresh_token)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"detail": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=e)


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
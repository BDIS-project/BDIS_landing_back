from django.db import connection, transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import hashlib

from .permissions import IsCashier, IsManager

import random
import string
from decimal import Decimal
from datetime import datetime, timedelta

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
      
def generate_unique_upc():
    """Generate a unique 12-character UPC."""
    while True:
        new_upc = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Store_Product WHERE UPC = %s OR UPC_prom = %s;", [new_upc, new_upc])
            if not cursor.fetchone():
                return new_upc


def process_store_products():
    """Process all rows in the Store_Product table 
    and create promotional products if conditions are met."""
    critical_products_number = 100
    critical_expire_date = datetime.now().date() + timedelta(days=5)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Store_Product;")
        rows = cursor.fetchall()

        for row in rows:
            UPC, UPC_prom, id_product, selling_price, products_number, expire_date, promotional_product = row
            
            # Enforce single normal and promotional product
            if promotional_product:
                cursor.execute("""
                    SELECT 1 FROM Store_Product 
                    WHERE id_product = %s AND promotional_product AND UPC != %s
                """, [id_product, UPC])
                if cursor.fetchone():
                    print(f'A promotional product already exists for id_product {id_product}')
                    continue
            else:
                cursor.execute("""
                    SELECT 1 FROM Store_Product 
                    WHERE id_product = %s AND NOT promotional_product AND UPC != %s
                """, [id_product, UPC])
                if cursor.fetchone():
                    print(f'A normal product already exists for id_product {id_product}')
                    continue

            # Check conditions for creating promotional products
            if products_number > critical_products_number and expire_date < critical_expire_date:
                cursor.execute("""
                    SELECT 1 FROM Store_Product WHERE UPC_prom = %s;
                """, [UPC])
                if not cursor.fetchone():
                    # Generate new unique UPC
                    new_upc = generate_unique_upc()

                    # Insert promotional product
                    cursor.execute("""
                        INSERT INTO Store_Product (UPC, UPC_prom, id_product, selling_price, products_number, expire_date, promotional_product)
                        VALUES (%s, %s, %s, %s, %s, %s, TRUE);
                    """, [new_upc, UPC, id_product, selling_price * Decimal('0.8'), products_number, expire_date])

                    # Set non-promotional products_number to 0
                    cursor.execute("""
                        UPDATE Store_Product
                        SET products_number = 0
                        WHERE UPC = %s;
                    """, [UPC])


class CreateCategoryAPIView(APIView):
    """
    API view to create Categories for MANAGER
    """
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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


class ProductNamesAPIView(APIView):
    """
    API view to retrive Products names and pk DROPDOWN LIST for MANAGER
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query = "SELECT id_product, product_name FROM Product ORDER BY product_name;"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            products = cursor.fetchall()
            product_names = [col[0] for col in cursor.description]

        result = [dict(zip(product_names, product)) for product in products]

        return Response(result, status=status.HTTP_200_OK)
    

class CreateStoreProductAPIView(APIView):
    """
    API view to create Store Products for MANAGER
    """
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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


class AboutMeAPIView(APIView):
    """
    API view to rethrive all info about CASHIER
    currently loggen in
    """
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        id_employee = request.GET.get('id')
        employee_query = """SELECT * FROM EMPLOYEE
        WHERE id_employee = %s;
        """
        check_query = """ SELECT * FROM Check_Table
        WHERE id_employee = %s;
        """
        params = [id_employee]

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


class ReportsAPIView(APIView):
    pass

# APIS for report
class StatisticsAPIView(APIView):
    pass

# Evelina
class CategoriesSummaryAPIView(APIView):

    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        API view to retrive info about
        average price of available products in each category.
        """

        query = """
        SELECT 
        Category.category_number, 
        Category.category_name, 
        COALESCE(AVG(Store_Product.selling_price), 0) AS avg_selling_price
        FROM 
        Category 
        LEFT JOIN Product ON Category.category_number = Product.category_number
        LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
        GROUP BY 
        Category.category_number, Category.category_name
        ORDER BY 
        Category.category_number;"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)

# Andrii
class AllProductsAreSold(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        API view to retrive info about
        average price of available products in each category.
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
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        API view to retrive info about
        all categories, sorted by name
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
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        API view to get 
        complete info about categories and all the products
        """

        query = """
        SELECT c.category_number, c.category_name, COALESCE(SUM(products_number),0) AS count
        FROM (Category AS c LEFT JOIN Product ON c.category_number = Product.category_number)
        LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
        GROUP BY c.category_number, c.category_name
        ORDER BY c.category_number, c.category_name;"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return Response(result, status=status.HTTP_200_OK)


class DeleteCategoryAPIView(APIView):
    """
    API view to delete Category for MANAGER
    """
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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

    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    pass


class CheckOverviewAPIView(APIView):
    """
    API view to retrieve store products using raw SQL for CASHIER
    """
    
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
    API view to retrieve store products using raw SQL for CASHIER
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
    API view to retrieve, update all categories using raw SQL 
    for MANAGER and CreateProductAPIView DROPDOWN LIST
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        query = "SELECT category_number, category_name FROM Category ORDER BY category_name;"
        
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
    API view to retrive, update products using raw sql FOR CASHIER
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
    API view to look over store using raw SQL for MANAGER.
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
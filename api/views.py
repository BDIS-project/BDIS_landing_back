from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

'''
The APIView class is a part of the Django Rest Framework (DRF). 
It provides a base class for all the API views and offers several advantages over standard Django views.

APIView provides built-in methods for handling different HTTP methods like get, post, put, patch, delete, etc.

APIView integrates with DRF's Request and Response classes, which provide additional functionality 
over Django's standard HttpRequest and HttpResponse.
DRF's Request class extends the standard request, adding support for parsing request data, such as JSON.
DRF's Response class simplifies returning JSON responses.

self: Refers to the instance of the class. 
It allows access to the attributes and methods of the class in the get method

request: An instance of rest_framework.request.Request.
This is an extended version of Django's HttpRequest. It includes additional features like:
.data: for accessing parsed request data.
.query_params: for accessing query parameters.
.user: for accessing the authenticated user.
.auth: for accessing the authentication context.

*args:
Variable-length argument list. It captures additional positional arguments passed to the method.
It is a way to accept any number of additional positional arguments.

**kwargs:
Variable-length keyword argument dictionary. It captures additional keyword arguments passed to the method.
It is a way to accept any number of additional keyword arguments.
Commonly used to pass URL parameters captured in Django URL patterns.

product_name = request.GET.get('product_name')

request:
Represents the HTTP request object. In the context of Django and Django Rest Framework (DRF), 
it contains all the information about the HTTP request made to the server.
It is an instance of rest_framework.request.Request in DRF, which extends Django's HttpRequest.

GET:
request.GET is a dictionary-like object in Django that contains all the query parameters of the GET request.
These query parameters are the key-value pairs included in the URL after the ? symbol.
For example, in the URL http://example.com/api/products?product_name=Tomato, the query parameter 
is product_name=Tomato.

.get('product_name'):
The .get() method is used to retrieve the value of a specific query parameter from the request.GET dictionary.
In this case, 'product_name' is the key for which we want to get the value.
.get() returns the value associated with the key 'product_name' if it exists in the query parameters.
If the key does not exist, it returns None.

%s:
This is a placeholder used in SQL queries for parameter substitution.
In the context of Python's cursor.execute(), 
the %s placeholder is replaced with the actual value in a safe manner to prevent SQL injection.

{}:
This is a placeholder for Python's str.format() method.
It allows dynamic insertion of values into the query string.
Example: "ORDER BY {};" can be formatted with a column name to dynamically specify the ORDER BY column.
Usage: query.format('product_name') would result in ORDER BY product_name.

with connection.cursor() as cursor:
This is a context manager that ensures proper resource management.
connection.cursor() opens a new database cursor.
The cursor is used to execute SQL commands and fetch results.
as cursor assigns the cursor object to the variable cursor.
When the block inside the with statement is exited, the cursor is automatically closed.

cursor.execute(queries['all_products']):
Executes the SQL query stored in queries['all_products'].

products = cursor.fetchall():
Fetches all rows from the executed query result.
fetchall() returns a list of tuples, where each tuple represents a row in the result set.

product_columns = [col[0] for col in cursor.description]:
cursor.description provides metadata about the columns in the result set.
It is a list of tuples, where each tuple contains information about a column.
col[0] accesses the first element of each tuple, which is the column name.
This list comprehension creates a list of column names.

product_list = [dict(zip(product_columns, product)) for product in products]:
Converts each tuple in products to a dictionary.
zip(product_columns, product) pairs each column name with the corresponding value from the row tuple.
dict() creates a dictionary from these pairs.
The list comprehension applies this transformation to each row in products.

product_list = [dict(zip(product_columns, product)) for product in products]:
Converts each tuple in products to a dictionary.
zip(product_columns, product) pairs each column name with the corresponding value from the row tuple.
dict() creates a dictionary from these pairs.
The list comprehension applies this transformation to each row in products.
'''

from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class StoreProductsAPIView(APIView):
    """
    API view to retrieve store products using raw SQL.
    """
    def get(self, request, *args, **kwargs):
        upc = request.GET.get('upc')
        product_name = request.GET.get('product_name')
        category_name = request.GET.get('category_name')
        promotional = request.GET.get('promotional')
        sort_by = request.GET.get('sort_by', 'product_name')

        queries = {
            'all_products': (
                "SELECT Product.*, category_name "
                "FROM Product INNER JOIN Category ON Product.category_number = Category.category_number "
                "ORDER BY product_name;"
            ),
            'all_store_products': (
                "SELECT Store_Product.*, product_name, category_name "
                "FROM Store_Product INNER JOIN Product ON Store_Product.id_product = Product.id_product "
                "INNER JOIN Category ON Product.category_number = Category.category_number "
                "ORDER BY product_name;"
            ),
            'product_by_upc': (
                "SELECT selling_price, products_number "
                "FROM Store_Product "
                "WHERE UPC = %s;"
            ),
            'product_by_name': (
                "SELECT Product.*, category_name " 
                "FROM Product INNER JOIN Category ON Product.category_number = Category.category_number "
                "WHERE product_name = %s;"
            ),
            'products_by_category': (
                "SELECT Product.* FROM Product "
                "INNER JOIN Category ON Product.category_number = Category.category_number "
                "WHERE category_name = %s "
                "ORDER BY product_name;"
            ),
            'promotional_products': (
                "SELECT Store_Product.*, product_name, category_name "
                "FROM Store_Product INNER JOIN Product ON Store_Product.id_product = Product.id_product "
                "INNER JOIN Category ON Product.category_number = Category.category_number "
                "WHERE promotional_product = TRUE "
                "ORDER BY {};"
            ),
            'non_promotional_products': (
                "SELECT Store_Product.*, product_name, category_name "
                "FROM Store_Product INNER JOIN Product ON Store_Product.id_product = Product.id_product "
                "INNER JOIN Category ON Product.category_number = Category.category_number "
                "WHERE promotional_product = FALSE "
                "ORDER BY {};"
            )
        }

        if upc:
            query = queries['product_by_upc']
            params = [upc]
        elif product_name:
            query = queries['product_by_name']
            params = [product_name]
        elif category_name:
            query = queries['products_by_category']
            params = [category_name]
        elif promotional == 'true':
            query = queries['promotional_products'].format(sort_by)
            params = []
        elif promotional == 'false':
            query = queries['non_promotional_products'].format(sort_by)
            params = []
        else:
            with connection.cursor() as cursor:
                cursor.execute(queries['all_products'])
                products = cursor.fetchall()
                product_columns = [col[0] for col in cursor.description]

            with connection.cursor() as cursor:
                cursor.execute(queries['all_store_products'])
                store_products = cursor.fetchall()
                store_products_columns = [col[0] for col in cursor.description]

            product_list = [dict(zip(product_columns, product)) for product in products]
            store_product_list = []

            for store_product in store_products:
                store_product = dict(zip(store_products_columns, store_product))
                if store_product['promotional_product']:
                    store_product['original_price'] = round(float(store_product['selling_price']) / 0.8, 2)
                store_product['selling_price'] = round(float(store_product['selling_price']), 2)
                store_product_list.append(store_product)

            result = {
                'products': product_list,
                'store_products': store_product_list
            }
            
            return Response(result, status=status.HTTP_200_OK)
        
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
    
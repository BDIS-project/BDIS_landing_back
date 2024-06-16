from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

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
    
class StoreProducts2APIView(APIView):
    """
    API view to retrieve store products using raw SQL.
    """
    def get(self, request, *args, **kwargs):
        upc = request.GET.get('upc')
        product_name = request.GET.get('product_name')
        category_name = request.GET.get('category_name')
        promotional = request.GET.get('promotional')
        min_price = request.GET.get('minPrice')
        max_price = request.GET.get('maxPrice')
        categories = request.GET.get('categories')
        in_stock = request.GET.get('inStock')
        sort_by = request.GET.get('sort', 'product_name')

        sort_by_column = 'product_name'
        sort_by_direction = 'ASC'

        if sort_by:
            if sort_by.endswith('-desc'):
                sort_by_column = sort_by[:-5]
                sort_by_direction = 'DESC'
            elif sort_by.endswith('-asc'):
                sort_by_column = sort_by[:-4]
                sort_by_direction = 'ASC'
            else:
                sort_by_column = sort_by

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
            query_conditions.append("AND product_name = %s")
            params.append(product_name)
        if category_name:
            query_conditions.append("AND category_name = %s")
            params.append(category_name)
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

        query = base_query + ' '.join(query_conditions) + f" ORDER BY {sort_by_column} {sort_by_direction};"

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
    def get(self, request, *args, **kwargs):
        query = "SELECT category_name FROM Category ORDER BY category_name;"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        category_names = [row[0] for row in rows]

        return Response(category_names, status=status.HTTP_200_OK)
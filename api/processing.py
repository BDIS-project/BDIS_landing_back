from django.db import connection, IntegrityError
import random
import string
from decimal import Decimal
from datetime import datetime, timedelta

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

                    try:
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

                    except IntegrityError as e:
                        print(f'Error inserting promotional product for id_product {id_product}: {e}')
                        continue
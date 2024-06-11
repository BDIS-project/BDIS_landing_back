from django.db import connection

def my_custom_sql(self):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * 
        FROM table_name 
        WHERE id=1
        """)
    row = cursor.fetchall()
    return row
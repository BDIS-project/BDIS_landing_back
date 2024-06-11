from django.db import models

class Category(models.Model):
    category_number = models.IntegerField(primary_key=True)
    category_name = models.CharField(max_length=50)

class Product(models.Model):
    id_product = models.AutoField(primary_key=True)
    category_number = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column='category_number')
    product_name = models.CharField(max_length=50)
    characteristics = models.CharField(max_length=100)

class StoreProduct(models.Model):
    UPC = models.CharField(max_length=12, primary_key=True)
    UPC_prom = models.ForeignKey('self', on_delete=models.SET_NULL, to_field='UPC', related_name='promoted_products', null=True, blank=True)
    id_product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, db_column='id_product')
    selling_price = models.DecimalField(max_digits=13, decimal_places=4)
    products_number = models.IntegerField()
    promotional_product = models.BooleanField()

    class Meta:
        verbose_name = 'Store Product'
        verbose_name_plural = 'Store Products'

class Employee(models.Model):
    id_employee = models.CharField(max_length=10, primary_key=True)
    empl_surname = models.CharField(max_length=50)
    empl_name = models.CharField(max_length=50)
    empl_patronymic = models.CharField(max_length=50)
    empl_role = models.CharField(max_length=10)
    salary = models.DecimalField(max_digits=13, decimal_places=4)
    date_of_birth = models.DateField()
    date_of_start = models.DateField()
    phone_number = models.CharField(max_length=13)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=9)

class Check(models.Model):
    check_number = models.CharField(max_length=10, primary_key=True)
    id_employee = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, db_column='id_employee')
    card_number = models.ForeignKey('CustomerCard', on_delete=models.DO_NOTHING, db_column='card_number', null=True, blank=True)
    print_date = models.DateTimeField()
    sum_total = models.DecimalField(max_digits=13, decimal_places=4)
    vat = models.DecimalField(max_digits=13, decimal_places=4)

class CustomerCard(models.Model):
    card_number = models.CharField(max_length=13, primary_key=True)
    cust_surname = models.CharField(max_length=50)
    cust_name = models.CharField(max_length=50)
    cust_patronymic = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=13)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=9)
    percent = models.IntegerField()

class Sale(models.Model):
    UPC = models.ForeignKey(StoreProduct, on_delete=models.DO_NOTHING, db_column='UPC')
    check_number = models.ForeignKey(Check, on_delete=models.CASCADE, db_column='check_number')
    product_number = models.IntegerField()
    selling_price = models.DecimalField(max_digits=13, decimal_places=4)

    class Meta:
        unique_together = (('UPC', 'check_number'),)

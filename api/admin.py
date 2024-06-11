from django.contrib import admin
from .models import Category, Product, StoreProduct, Employee, Check, CustomerCard, Sale

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_number', 'category_name')
    search_fields = ('category_name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id_product', 'category_number', 'product_name', 'characteristics')
    search_fields = ('product_name',)
    list_filter = ('category_number',)

@admin.register(StoreProduct)
class StoreProductAdmin(admin.ModelAdmin):
    list_display = ('UPC', 'id_product', 'selling_price', 'products_number', 'promotional_product')
    search_fields = ('UPC', 'id_product__product_name')
    list_filter = ('promotional_product',)
    readonly_fields = ('selling_price',)  # Example of making a field read-only

    def formatted_selling_price(self, obj):
        return "${:,.2f}".format(obj.selling_price)
    formatted_selling_price.short_description = 'Selling Price'

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id_employee', 'empl_surname', 'empl_name', 'empl_role', 'salary', 'phone_number')
    search_fields = ('empl_surname', 'empl_name', 'empl_role')
    list_filter = ('empl_role',)

@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ('check_number', 'id_employee', 'card_number', 'print_date', 'sum_total', 'vat')
    search_fields = ('check_number', 'id_employee__empl_surname')
    list_filter = ('print_date',)

@admin.register(CustomerCard)
class CustomerCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'cust_surname', 'cust_name', 'phone_number', 'percent')
    search_fields = ('cust_surname', 'cust_name', 'phone_number')
    list_filter = ('percent',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('UPC', 'check_number', 'product_number', 'selling_price')
    search_fields = ('UPC__UPC', 'check_number__check_number')
    list_filter = ('UPC__promotional_product',)

    def formatted_selling_price(self, obj):
        return "${:,.2f}".format(obj.selling_price)
    formatted_selling_price.short_description = 'Selling Price'

    list_display = ('UPC', 'check_number', 'product_number', 'formatted_selling_price')

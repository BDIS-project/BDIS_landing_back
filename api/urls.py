from django.urls import path
from api.views import * 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from django.contrib import admin
from django.urls import path, include

urlpatterns = [

    # urls for DQL-queries
    path('products/', ProductsAPIView.as_view(), name = 'products'), # CASHIER
    path('store-products/', StoreProductsAPIView.as_view(), name='store-products'), # CASHIER
    path('check-overview/', CheckOverviewAPIView.as_view(), name = 'check-overview'), # CASHIER
    path('categories/', CategoriesAPIView.as_view(), name='get_categories'), # CASHIER, DROPDOWN LIST
    path('product-names/', ProductNamesAPIView.as_view(), name = 'product-names'), # DROPDOWN LIST
    path('store-overview/', StoreOverviewAPIView.as_view(), name = 'store-overview'), # MANAGER
    path('about-me/', AboutMeAPIView.as_view(), name = 'about-me'), # CASHIER
    path('reports/', ReportsAPIView.as_view(), name = 'reports'), # MANAGER
    path('customer-card-overview/', CustomerCardOverviewAPIView.as_view(), name = 'customer-card-overview'), # MANAGER
    path('manager-store-overview/', ManagerStoreOverviewAPIView.as_view(), name = 'manager-store-overview'), # MANAGER

    # urls for entities creation for MANAGER
    path('create-category/', CreateCategoryAPIView.as_view(), name = 'create-category'),
    path('create-product/', CreateProductAPIView.as_view(), name = 'create-product'),
    path('create-store-product/', CreateStoreProductAPIView.as_view(), name = 'create-store-product'),
    path('create-employee/', CreateEmployeeAPIView.as_view(), name = 'create-employee'),
    path('create-customer/', CreateCustomerAPIView.as_view(), name = 'create-customer'), # and CASHIER
    path('customer-percent/', CustumerPercentAPIView.as_view(), name = 'customer-percent'), # DROPDOWN LIST
    path('create-check/', CreateCheckAPIView.as_view(), name = 'create-check'),

    # urls for updating
    path('categories/<int:category_number>/updateCategory/', CategoriesAPIView.as_view(), name='update_category'), 
    path('products/<int:id_product>/updateProduct/', ProductsAPIView.as_view(), name='update_product'), 
    path('store-products/<str:UPC>/updateStoreProduct/', StoreProductsAPIView.as_view(), name='update_store_product'),
    path('employee/<str:id_employee>/updateEmployee/', UpdateEmployeeAPIView.as_view(), name='update_employee'),
    path('employee', UpdateEmployeeAPIView.as_view(), name='get_employee'),

    # urls for entities deletion for MANAGER
    path('delete-category/<int:category_number>/', DeleteCategoryAPIView.as_view(), name='delete-category'),
    path('delete-product/<int:id_product>/', DeleteProductAPIView.as_view(), name = 'delete-product'),
    path('delete-store-product/<str:UPC>/', DeleteStoreProductAPIView.as_view(), name = 'delete-store-product'),
    path('delete-employee/<str:id_employee>/', DeleteEmployeeAPIView.as_view(), name = 'delete-employee'),
    path('delete-customer/<str:card_number>/', DeleteCustomerAPIView.as_view(), name = 'delete-customer'),
    path('delete-check', DeleteCheckAPIView.as_view(), name = 'delete-check'),

    # urls for the report
    path('statistics/', StatisticsAPIView.as_view(), name='statistics'),
    path('categories-summary/', CategoriesSummaryAPIView.as_view(), name='categories-revenue'), # Evelina
    path('sold-every-product/', SoldEveryProductAPIView.as_view(), name='sold-every-product'), # Evelina
    path('category-average-price/', CategoryAveragePrice.as_view(), name='category-average-price'), # Andrii
    path('all-products-are-sold/', AllProductsAreSold.as_view(), name='all-products-are-sold'), # Andrii
    path('all-categories/', AllCategories.as_view(), name='all-categories'), # Damian
    path('category-products-info/', CategoryProductInfo.as_view(), name='category-products-info'), # Damian
    
    # urls for authentification
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # urls for token usage 
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('test-token/', TestTokenView.as_view(), name='test_token'),
]

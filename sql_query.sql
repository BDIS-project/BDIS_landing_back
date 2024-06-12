-- Test query 1
SELECT category_name, SUM(product_number) AS total_units_sold, SUM(Sale.selling_price) AS total_revenue
FROM ((Sale INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC) INNER JOIN Product ON Store_Product.id_product = Product.id_product) INNER JOIN Category ON Product.category_number = Category.category_number
GROUP BY Category.category_name;

-- MANAGER --
-- 5. Get info about all Employee, sorted by surname;
SELECT *
FROM Employee
ORDER BY empl_surname;

-- 6. Get info about all Employee with the role 'Sale', sorted by surname;
SELECT * 
FROM Employee
WHERE (empl_role = 'sales')
ORDER BY empl_surname;

-- 7. Get info about all regular customers, sorted by surname;
SELECT * 
FROM Customer_Card
ORDER BY cust_surname;

-- 8. Get info about all categoris, sorted by name;
SELECT * 
FROM Category
ORDER BY category_name;

-- 9. Get info about all products, sorted by name;
SELECT * 
FROM Product
ORDER BY product_name;

-- 10. Get info about all store products, sorted by product number;
SELECT product_name, selling_price, products_number, promotional_product
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
ORDER BY products_number;

-- 11. For given employee surname, find his telephone and address;
SELECT phone_number, city, street
FROM Employee
WHERE empl_surname = 'Kovalenko';

-- 12. Get info about all regular customers, 
-- that have customer card with certain percent sorted by surname;
SELECT *
FROM Customer_Card
WHERE percent = 3
ORDER BY cust_surname;

-- 13. Find all products that belong to certain category, sorted by name;
SELECT *
FROM Product INNER JOIN Category ON Product.category_number = Category.category_number
WHERE category_name = 'Sweets'
ORDER BY product_name;

-- 14. For given UPC find product price, product number, name and characteristics
SELECT selling_price, Store_Product.products_number, product_name, characteristics
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE UPC = '101234567890';

-- 15.1. Get info about all promotional store products, sorted by product number;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = TRUE
ORDER BY Store_Product.products_number;

-- 15.2. Get info about all promotional store products, sorted by name;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = TRUE
ORDER BY product_name;

-- 16.1. Get info about all non promotional store products, sorted by product number;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = FALSE
ORDER BY product_name;

-- 16.2. Get info about all non promotional store products, sorted by name;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = FALSE
ORDER BY product_name;

-- 17. Отримати інформацію про усі чеки, створені певним касиром за певний період часу 
-- (з можливістю перегляду куплених товарів у цьому чеку, їх назви, к-сті та ціни);

-- 18. Отримати інформацію про усі чеки, створені усіма касирами за певний період часу 
-- (з можливістю перегляду куплених товарів у цьому чеку, їх назва, к-сті та ціни);

-- 19. Визначити загальну суму проданих товарів з чеків, створених певним касиром за
-- певний період часу;

-- 20. Визначити загальну суму проданих товарів з чеків, створених усіма касиром за
-- певний період часу;

-- 21. Визначити загальну кількість одиниць певного товару, проданого за певний
-- період часу.

-- CASHIER --
-- 1. Get info about all products, sorted by name;
SELECT * 
FROM Product
ORDER BY product_name;

-- 2. Get info about all store products, sorted by name;
SELECT product_name, selling_price, products_number, promotional_product
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
ORDER BY product_name;

-- 3. Get info about all regular customers, sorted by surname;
SELECT * 
FROM Customer_Card
ORDER BY cust_surname;

-- 4. Search for products by name;
SELECT *
FROM Product
WHERE product_name = 'Tomato';

-- 5. Find all products that belong to certain category, sorted by name;
SELECT *
FROM Product INNER JOIN Category ON Product.category_number = Category.category_number
WHERE category_name = 'Sweets'
ORDER BY product_name;

-- 6. Get info about all regular customers, sorted by surname;
SELECT * 
FROM Customer_Card
ORDER BY cust_surname;

-- 7. Selling goods (adding checks);
-- 8. Insert/update info about regular clients;

-- 9. View list of all checks cashier created today;
SELECT * 
FROM Check_Table
WHERE id_employee = '1001' AND print_date::date = CURRENT_DATE;

-- 10. View list of all checks cashier created for a certain period of time;
SELECT * 
FROM Check_Table
WHERE id_employee = '1001'
AND print_date >= '2024-06-01'
AND print_date < '2024-06-12';

-- 11. For a given check number get all info about this check, including info about products names,
-- number and price;
SELECT Check_Table.check_number, id_employee, card_number, print_date, sum_total, vat,
Product.product_name, Sale.selling_price, Sale.product_number
FROM Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
INNER JOIN Product ON Store_Product.id_product = Product.id_product
WHERE Check_Table.check_number = '100001';

-- 12.1. Get info about all promotional store products, sorted by product number;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = TRUE
ORDER BY Store_Product.products_number;

-- 12.2. Get info about all promotional store products, sorted by name;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = TRUE
ORDER BY product_name;

-- 13.1. Get info about all non promotional store products, sorted by product number;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = FALSE
ORDER BY product_name;

-- 13.2. Get info about all non promotional store products, sorted by name;
SELECT *
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
WHERE promotional_product = FALSE
ORDER BY product_name;

-- 14. For given UPC find product price and product number
SELECT selling_price, products_number
FROM Store_Product
WHERE UPC = '101234567890';

-- 15. Get all info about yourself
SELECT * FROM Check_Table;
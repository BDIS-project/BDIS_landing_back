-- Test query 1
SELECT category_name, SUM(product_number) AS total_units_sold, SUM(Sale.selling_price) AS total_revenue
FROM ((Sale INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC) INNER JOIN Product ON Store_Product.id_product = Product.id_product) INNER JOIN Category ON Product.category_number = Category.category_number
GROUP BY Category.category_name;
-- Отримати інформацію про усіх працівників, відсортованих за прізвищем;
SELECT *
FROM Employee
ORDER BY empl_surname;

-- Отримати інформацію про усіх працівників, що займають посаду касира,відсортованих за прізвищем;
SELECT * 
FROM Employee
WHERE (empl_role = 'sales')
ORDER BY empl_surname;

-- Отримати інформацію про усіх постійних клієнтів, відсортованих за прізвищем;
SELECT * 
FROM Customer_Card
ORDER BY cust_surname;

-- Отримати інформацію про усі категорії, відсортовані за назвою;
SELECT * 
FROM Category
ORDER BY category_name;

-- Отримати інформацію про усі товари, відсортовані за назвою;
SELECT * 
FROM Product
ORDER BY product_name;

-- Отримати інформацію про усі товари у магазині, відсортовані за кількістю;
SELECT product_name, selling_price, products_number, promotional_product
FROM Store_Product JOIN Product ON Store_Product.id_product = Product.id_product
ORDER BY products_number;

-- За прізвищем працівника знайти його телефон та адресу;
-- Отримати інформацію про усіх постійних клієнтів, що мають карту клієнта із
-- певним відсотком, посортованих за прізвищем;
-- Здійснити пошук усіх товарів, що належать певній категорії, відсортованих за назвою;
-- За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару, назву та характеристики товару;
-- Отримати інформацію про усі акційні товари, відсортовані за кількістю одиниць товару/ за назвою;

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
WHERE NOT EXISTS (  SELECT *
                    FROM Product
                    WHERE id_product NOT IN ( SELECT id_product
                                              FROM Store_Product
                                            ) 
                    AND Category.category_number = Product.category_number
                 )
ORDER BY category_number, category_name;

-- Отримати список категій та кількість продуктів в них
SELECT c.category_number, c.category_name, Nz(SUM(product_number),0) AS [count]
FROM (Category AS c LEFT JOIN Product ON c.category_number = Product.category_number) LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
GROUP BY c.category_number, c.category_name
ORDER BY c.category_number, c.category_name;

------------------------------------------------------------------------------------

-- Функціональні вимоги за типами користувачів
-- Менеджер:
    1. Додавати нові дані про працівників, постійних клієнтів, категорії товарів, товари, 
    товари у магазині;
        1.1 Додавати нові дані про працівників
            INSERT INTO Employee (id_employee, empl_surname, empl_name, empl_patronymic, 
                                  empl_role, salary, date_of_birth, date_of_start, 
                                  phone_number, city, street, zip_code) 
            VALUES (1001, 'Kovalenko', 'Anatoliy', 'Vasylovych',
                    'sales', 1000, '1984-12-03', '2005-01-09',
                    '+380678541234', 'Kyiv', 'Hrushevskoho', '00100')

    2. Редагувати дані про працівників, постійних клієнтів, категорії товарів, товари, 
    товари у магазині;

    3. Видаляти дані про працівників, постійних клієнтів, категорії товарів, товари, 
    товари у магазині, чеки;

    4. Видруковувати звіти з інформацією про усіх працівників, постійних клієнтів, 
    категорії товарів, товари, товари у магазині, чеки;

    5. Отримати інформацію про усіх працівників, відсортованих за прізвищем;
        SELECT * 
        FROM Employee
        ORDER BY empl_surname, empl_name;

    6. Отримати інформацію про усіх працівників, що займають посаду касира, 
    відсортованих за прізвищем;
        SELECT * 
        FROM Employee
        WHERE empl_role = "sales"
        ORDER BY empl_surname, empl_name;

    7. Отримати інформацію про усіх постійних клієнтів, відсортованих за прізвищем;

    8. Отримати інформацію про усі категорії, відсортовані за назвою;
        SELECT * 
        FROM Category
        ORDER BY category_name;

    9. Отримати інформацію про усі товари, відсортовані за назвою;
        SELECT id_product, product_name, (SELECT category_name 
              from Category 
              where Product.category_number = Category.category_number)
              , characteristics
        FROM Product
        ORDER BY product_name;


    10. Отримати інформацію про усі товари у магазині, відсортовані за кількістю;
        SELECT Product.id_product, product_name, category_name, selling_price, product_number
        FROM (Category INNER JOIN Product ON Category.category_number = Product.category_number) 
              INNER JOIN Store_Product ON Product.id_product = Store_Product.id_product
        ORDER BY product_number;


    11. За прізвищем працівника знайти його телефон та адресу;
        SELECT id_employee, empl_surname, empl_name, phone_number, city, street
        FROM Employee
        WHERE empl_surname = "place holder from empl surname";

    12. Отримати інформацію про усіх постійних клієнтів, що мають карту клієнта із 
    певним відсотком, посортованих за прізвищем;
        SELECT cust_surname, cust_name, phone_number, city, street
        FROM Customer_Card
        WHERE percent = "place holder for the client`s percentage";

    13. Здійснити пошук усіх товарів, що належать певній категорії, відсортованих за назвою;
        SELECT id_product, product_name
        FROM Product
        WHERE category_number IN 
           (SELECT category_name
           FROM Category
           WHERE category_name = "place holder for category name")
        ORDER BY product_name;

    14. За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару,
    назву та характеристики товару;
        SELECT id_product, product_name, characteristics, selling_price, product_number
        FROM Product INNER JOIN Store_Product ON Product.id_product = Store_Product.id_product
        WHERE UPC = "place holder for UPC";

    15. Отримати інформацію про усі акційні товари, відсортовані за кількістю одиниць 
    товару/ за назвою;
        SELECT id_product, product_name, characteristics, selling_price, product_number
        FROM Product INNER JOIN Store_Product ON Product.id_product = Store_Product.id_product
        WHERE promotional_product = TRUE
        ORDER BY products_number, product_name;


    16. Отримати інформацію про усі не акційні товари, відсортовані за кількістю 
    одиниць товару/ за назвою;
        SELECT id_product, product_name, characteristics, selling_price, product_number
        FROM Product INNER JOIN Store_Product ON Product.id_product = Store_Product.id_product
        WHERE promotional_product = FALSE
        ORDER BY products_number, product_name;

    17. Отримати інформацію про усі чеки, створені певним касиром за певний період 
    часу (з можливістю перегляду куплених товарів у цьому чеку, їх назви, к-сті та ціни);

    18. Отримати інформацію про усі чеки, створені усіма касирами за певний період 
    часу (з можливістю перегляду куплених товарів у цьому чеку, їх назва, к-сті та ціни);

    19. Визначити загальну суму проданих товарів з чеків, створених певним касиром за 
    певний період часу;

    20. Визначити загальну суму проданих товарів з чеків, створених усіма касиром за 
    певний період часу;

    21. Визначити загальну кількість одиниць певного товару, проданого за певний 
    період часу.


Касир:
    1. Отримати інформацію про усі товари, відсортовані за назвою;
        SELECT * 
        FROM Product
        ORDER BY product_name;

    2. Отримати інформацію про усі товари у магазині, відсортовані за назвою;

    3. Отримати інформацію про усіх постійних клієнтів, відсортованих за прізвищем;
        SELECT * 
        FROM Customer_Card
        ORDER BY cust_surname;

    4. Здійснити пошук товарів за назвою;
        SELECT id_product, product_name, characteristics
        FROM Product
        WHERE product_name = "place holder for product name";

    5. Здійснити пошук товарів, що належать певній категорії, відсортованих за назвою;
        SELECT id_product, product_name, characteristics
        FROM Product
        WHERE category_number IN ( SELECT category_number
                                   FROM Category
                                   WHERE category_name = "place holder for category name"
                                 );

    6. Здійснити пошук постійних клієнтів за прізвищем;
        SELECT * 
        FROM Customer_Card
        ORDER BY cust_surname, cust_name;

    7. Здійснювати продаж товарів (додавання чеків);

    8. Додавати/редагувати інформацію про постійних клієнтів;

    9. Переглянути список усіх чеків, що створив касир за цей день;

    10. Переглянути список усіх чеків, що створив касир за певний період часу;

    11. За номером чеку вивести усю інформацію про даний чек, в тому числі 
    інформацію про назву, к-сть та ціну товарів, придбаних в даному чеку.

    12. Отримати інформацію про усі акційні товари, відсортовані за кількістю одиниць 
    товару/ за назвою;
        SELECT Product.id_product, product_name, characteristics, selling_price, product_number
        FROM Product INNER JOIN Store_Product ON Product.id_product = Store_Product.id_product
        WHERE promotional_product = TRUE
        ORDER BY product_number, product_name;

    13. Отримати інформацію про усі не акційні товарів, відсортовані за кількістю 
    одиниць товару/ за назвою;
        SELECT Product.id_product, product_name, characteristics, selling_price, product_number
        FROM Product INNER JOIN Store_Product ON Product.id_product = Store_Product.id_product
        WHERE promotional_product = FALSE
        ORDER BY product_number, product_name;

    14. За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару.
        SELECT selling_price, product_number
        FROM Store_Product
        WHERE UPC = "place holder for the given UPC";

    15. Можливість отримати усю інформацію про себе.
        SELECT *
        FROM Employee
        WHERE id_employee = "place holder";



<<<<<<< HEAD


=======
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

-- 17. Get info about all checks created by certain cashier in certain period of time
-- (with ability to view sold products in this check, their names, quantity and price); 
SELECT Check_Table.check_number, id_employee, card_number, print_date, sum_total, vat,
Product.product_name, Sale.selling_price, Sale.product_number
FROM Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
INNER JOIN Product ON Store_Product.id_product = Product.id_product
WHERE id_employee = '1001' AND print_date > '2024-06-10' AND print_date < '2024-06-15';

-- 18. Get info about all checks created by all cashiers in certain period of time
-- (with ability to view sold products in this check, their names, quantity and price); 
SELECT Check_Table.check_number, id_employee, card_number, print_date, sum_total, vat,
Product.product_name, Sale.selling_price, Sale.product_number
FROM Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
INNER JOIN Product ON Store_Product.id_product = Product.id_product
WHERE print_date > '2024-06-10' AND print_date < '2024-06-15';

-- 19. Get sum total of sold products from checks, created by certain cashier 
-- in certain period of time
SELECT SUM(sum_total)
FROM Check_Table
WHERE id_employee = '1001' AND print_date > '2024-06-10' AND print_date < '2024-06-15';

-- 20. Get sum total of sold products from checks, created by all cashiers
-- in certain period of time
SELECT SUM(sum_total)
FROM Check_Table
WHERE id_employee = '1001' AND print_date > '2024-06-10' AND print_date < '2024-06-15';

-- 21. Determite total number of certain product, sold for certain period of time
SELECT SUM(product_number)
FROM Check_Table INNER JOIN Sale ON Check_Table.check_number = Sale.check_number
INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC
INNER JOIN Product ON Store_Product.id_product = Product.id_product
WHERE product_name = 'Tomato' AND print_date > '2024-06-10' AND print_date < '2024-06-15';

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
WHERE id_employee = '1001' AND print_date > '2024-06-10' AND print_date < '2024-06-15';

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
>>>>>>> 6b48de792cfe234b4c7b4be3417f0ca651f6c21a

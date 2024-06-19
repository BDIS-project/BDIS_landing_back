-- SELECT * 
--         FROM Employee
--         ORDER BY empl_surname, empl_name;

SELECT c.category_number, c.category_name, SUM(products_number) as count
FROM (Category AS c LEFT JOIN Product ON c.category_number = Product.category_number) LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
GROUP BY c.category_number, c.category_name
ORDER BY c.category_number, c.category_name;
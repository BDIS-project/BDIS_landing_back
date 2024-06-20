-- Get complete info about categories and all the products
SELECT c.category_number, c.category_name, COALESCE(SUM(products_number),0) AS count
FROM (Category AS c LEFT JOIN Product ON c.category_number = Product.category_number) LEFT JOIN Store_Product ON Product.id_product = Store_Product.id_product
GROUP BY c.category_number, c.category_name
ORDER BY c.category_number, c.category_name;
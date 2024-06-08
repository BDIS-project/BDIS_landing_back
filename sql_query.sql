SELECT category_name, SUM(product_number) AS total_units_sold, SUM(Sale.selling_price) AS total_revenue
FROM ((Sale INNER JOIN Store_Product ON Sale.UPC = Store_Product.UPC) INNER JOIN Product ON Store_Product.id_product = Product.id_product) INNER JOIN Category ON Product.category_number = Category.category_number
GROUP BY Category.category_name;
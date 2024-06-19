-- Fill Category table
INSERT INTO Category (category_name) VALUES ('Vegetables');
INSERT INTO Category (category_name) VALUES ('Fruits');
INSERT INTO Category (category_name) VALUES ('Dairy_products');
INSERT INTO Category (category_name) VALUES ('Meat');
INSERT INTO Category (category_name) VALUES ('Sweets');

-- Fill Product table
INSERT INTO Product (category_number, product_name, characteristics) VALUES 
(1, 'Cucumber "Mirabella"', 'Green cucumber, variety "Mirabella"'),
(1, 'Tomato', 'Red tomato'),
(2, 'Banana', 'Yellow banana'),
(2, 'Apple "Golden"', 'Green apple, variety "Golden"'),
(3, 'Ryazhenka "Slovyanochka"', 'Product from baked milk'),
(3, 'Milk "Yahotynske"', 'Milk, 5% fat content'),
(4, 'Chicken fillet', 'Fresh fillet of young chicken'),
(4, 'Pork ribs', 'Pork ribs'),
(5, 'Cake "Napoleon"', 'Cake "Napoleon" by Roshen'),
(5, 'Candies "Red Poppy"', 'Candies "Red Poppy" by Roshen');

-- Fill Store_Product table
/*INSERT INTO Store_Product (UPC, UPC_prom, id_product, selling_price, products_number, promotional_product) VALUES 
('101234567890', NULL, 10, 14.45, 100, FALSE),
('123456789012', '123456789012', 11, 10.99, 21, TRUE),
('234567890123', '234567890123', 12, 15.11, 15, TRUE),
('345678901234', NULL, 13, 22.19, 60, FALSE),
('456789012345', NULL, 14, 18.93, 120, FALSE),
('567890123456', NULL, 15, 31.23, 15, FALSE),
('678901234567', '678901234567', 16, 28.28, 42, TRUE),
('789012345678', NULL, 17, 56.16, 15, FALSE),
('890123456789', NULL, 18, 190.98, 15, FALSE),
('901234567890', NULL, 19, 19.99, 5, FALSE);*/

INSERT INTO Store_Product (UPC, UPC_prom, id_product, selling_price, products_number, expire_date, promotional_product) VALUES 
('123456789012', NULL, 1, 14.45, 200, '2024-06-20', FALSE),
-- ('000000000000', '101234567890', 1, 10.99, 21, '2024-06-13', TRUE),
-- ('234567890123', '234567890123', 3, 15.11, 15, '2024-06-13', TRUE),
('345678901234', NULL, 4, 22.19, 60, '2024-06-13', FALSE),
('456789012345', NULL, 5, 18.93, 120, '2024-06-21', FALSE),
('567890123456', NULL, 6, 31.23, 15, '2024-06-13', FALSE),
-- ('678901234567', '678901234567', 7, 28.28, 42, '2024-06-13', TRUE),
('789012345678', NULL, 8, 56.16, 15, '2024-06-13', FALSE),
('890123456789', NULL, 9, 190.98, 15, '2024-06-13', FALSE),
('901234567890', NULL, 10, 19.99, 5, '2024-06-13', FALSE);

-- Fill Employee table
INSERT INTO Employee (id_employee, empl_surname, empl_name, empl_patronymic, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code) VALUES 
(1001, 'Kovalenko', 'Anatoliy', 'Vasylovych', 'Cashier', 1000, '1984-12-03', '2005-01-09', '+380678541234', 'Kyiv', 'Hrushevskoho', '00100'),
(1002, 'Honchar', 'Oksana', 'Petrovna', 'Cashier', 1200, '1978-07-24', '2000-05-15', '+380509876543', 'Lviv', 'Stepana Bandery', '00120'),
(1003, 'Savchuk', 'Yevheniya', 'Olehivna', 'Cashier', 500, '1992-09-11', '2014-03-20', '+380974567898', 'Odessa', 'Morska', '00130'),
(1004, 'Shevchenko', 'Mykola', 'Ivanovych', 'Cleaner', 510, '1986-05-02', '2007-12-10', '+380681234567', 'Kharkiv', 'Poltavskyi', '00140'),
(1005, 'Krushenytska', 'Iryna', 'Mykolayivna', 'Manager', 2000, '1989-09-30', '2010-05-07', '+380996754321', 'Zaporizhzhia', 'Shevchenka', '00150');

-- Fill User_Table table
INSERT INTO User_Table(username, user_password, id_employee) VALUES
('cashier01', 'password', 1001),
('cashier02', 'qwerty', 1002),
('manager01', 'pumpumpum', 1005);

-- Fill Customer_Card table
INSERT INTO Customer_Card (card_number, cust_surname, cust_name, cust_patronymic, phone_number, city, street, zip_code, percent) VALUES 
(101, 'Pavlova', 'Kristina', 'Sergiivna', '+380671234567', 'Boryspil', 'Kyivskyi Shliakh', '00091', 3),
(102, 'Zolota', 'Darina', NULL, '+380672234567', 'Kyiv', 'Khreshchatyk', '00092', 1),
(103, 'Pechurova', 'Evelina', 'Yanivna', '+380673434567', 'Lviv', 'Bandery', '00093', 2),
(104, 'Petrenko', 'Anton', NULL, '+380673434578', 'Odessa', 'Deribasivska', '00094', 2),
(105, 'Mykolaichuk', 'Maksym', 'Antonovych', '+380123434578', 'Kharkiv', 'Shevchenka', '00095', 1),
(106, 'Andriievych', 'Panas', 'Maksymovych', '+380986789012', 'Zaporizhzhia', 'Shevchenka', '00096', 3);

-- Fill Check_Table table
INSERT INTO Check_table (check_number, id_employee, card_number, print_date, sum_total) VALUES 
(100001, 1001, 102, '2024-06-12', 70.48),
(100002, 1001, 101, '2024-06-13', 484.81),
(100003, 1002, 103, '2024-06-10', 37.09),
(100004, 1002, 104, '2024-06-7', 340.74);

-- Fill Sales table
INSERT INTO Sale (UPC, check_number, product_number) VALUES
('123456789012', '100001', 1),
('123456789012', '100003', 2),
-- ('234567890123', '100001', 1),
('345678901234', '100002', 5),
('345678901234', '100004', 5),
('456789012345', '100002', 3),
('567890123456', '100002', 3),
('123456789012', '100002', 1),
('789012345678', '100002', 1),
('890123456789', '100002', 1),
('901234567890', '100002', 2);
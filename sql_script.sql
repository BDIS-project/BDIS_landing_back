-- create Category table
CREATE TABLE Category ( 
    category_number SERIAL PRIMARY KEY,  
    category_name VARCHAR(50) NOT NULL 
); 

-- create Product table
CREATE TABLE Product ( 
    id_product SERIAL PRIMARY KEY, 
    category_number INTEGER NOT NULL, 
    product_name VARCHAR(50) NOT NULL, 
    characteristics VARCHAR(100) NOT NULL,
    picture VARCHAR(100), 
    FOREIGN KEY (category_number) REFERENCES Category(category_number) 
        ON UPDATE CASCADE 
        ON DELETE NO ACTION 
); 

-- create Store_Product table
CREATE TABLE Store_Product ( 
    UPC VARCHAR(12) PRIMARY KEY NOT NULL, 
    UPC_prom VARCHAR(12), 
    id_product INTEGER NOT NULL,
    selling_price DECIMAL(13, 4) NOT NULL,
    products_number INTEGER NOT NULL,
    expire_date DATE NOT NULL,
    promotional_product BOOLEAN NOT NULL,
    CONSTRAINT positive_selling_price CHECK (selling_price > 0),
    CONSTRAINT not_negative_products_number CHECK (products_number > -1),
    FOREIGN KEY (UPC_prom) REFERENCES Store_Product(UPC)
        ON UPDATE CASCADE 
        ON DELETE SET NULL, 
    FOREIGN KEY (id_product) REFERENCES Product(id_product) 
        ON UPDATE CASCADE 
        ON DELETE NO ACTION,
    
    -- to ensure each id_product can only appear once as normal and once as promotional
    CONSTRAINT unique_product_promotional UNIQUE (id_product, promotional_product)
); 

-- create Employee table
CREATE TABLE Employee ( 
    id_employee VARCHAR(10) PRIMARY KEY NOT NULL,
    empl_surname VARCHAR(50) NOT NULL, 
    empl_name VARCHAR(50) NOT NULL, 
    empl_patronymic VARCHAR(50), 
    empl_role VARCHAR(10) NOT NULL, 
    salary DECIMAL(13, 4) NOT NULL 
    CONSTRAINT positive_salary CHECK (salary > 0), 
    date_of_birth DATE NOT NULL 
    CONSTRAINT adult_employee CHECK (date_of_birth <= CURRENT_DATE - INTERVAL '18 years'), 
    date_of_start DATE NOT NULL,
    phone_number VARCHAR(13) NOT NULL, 
    city VARCHAR(50) NOT NULL, 
    street VARCHAR(50) NOT NULL, 
    zip_code VARCHAR(9) NOT NULL 
); 

-- create User_Table table
CREATE TABLE User_Table (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    id_employee VARCHAR(10) NOT NULL, 
    FOREIGN KEY (id_employee) REFERENCES Employee(id_employee) 
        ON UPDATE CASCADE 
        ON DELETE NO ACTION
);

-- create Customer_Card table
CREATE TABLE Customer_Card ( 
    card_number VARCHAR(13) PRIMARY KEY NOT NULL, 
    cust_surname VARCHAR(50) NOT NULL, 
    cust_name VARCHAR(50) NOT NULL, 
    cust_patronymic VARCHAR(50), 
    phone_number VARCHAR(13) NOT NULL, 
    city VARCHAR(50), 
    street VARCHAR(50), 
    zip_code VARCHAR(9), 
    percent INTEGER NOT NULL 
    CONSTRAINT positive_percent CHECK (percent > 0) 
); 

-- Named Check_table because CHECK is a keyword in Postgres
CREATE TABLE Check_Table ( 
    check_number VARCHAR(10) PRIMARY KEY NOT NULL, 
    id_employee VARCHAR(10) NOT NULL, 
    card_number VARCHAR(13), 
    print_date TIMESTAMP NOT NULL, 
    sum_total DECIMAL(13, 4) NOT NULL, 
    vat DECIMAL(13, 4) GENERATED ALWAYS AS (sum_total * 0.2) STORED, 
    FOREIGN KEY (id_employee) REFERENCES Employee(id_employee) 
        ON UPDATE CASCADE 
        ON DELETE NO ACTION, 
    FOREIGN KEY (card_number) REFERENCES Customer_Card(card_number) 
        ON UPDATE CASCADE 
        ON DELETE NO ACTION 
); 

-- create Sale table
CREATE TABLE Sale ( 
    UPC VARCHAR(12) NOT NULL, 
    check_number VARCHAR(10) NOT NULL, 
    product_number INT NOT NULL, 
    selling_price DECIMAL(13, 4),
    CONSTRAINT positive_selling_price CHECK (selling_price > 0),
    PRIMARY KEY (UPC, check_number), 
    FOREIGN KEY (UPC) REFERENCES Store_Product(UPC) 
        ON UPDATE CASCADE 
        ON DELETE NO ACTION, 
    FOREIGN KEY (check_number) REFERENCES Check_Table(check_number) 
        ON UPDATE CASCADE 
        ON DELETE CASCADE 
); 

-- Function to store selling price of connected Store_Product
CREATE OR REPLACE FUNCTION set_selling_price()
RETURNS TRIGGER AS $$
DECLARE
    store_price DECIMAL(13, 4);
BEGIN
    -- Get the selling price from the Store_Product table
    SELECT selling_price INTO store_price
    FROM Store_Product
    WHERE UPC = NEW.UPC;

    -- Set the selling price in the Sale table
    NEW.selling_price := store_price;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers function to set Sale price
CREATE TRIGGER get_selling_price
BEFORE INSERT OR UPDATE ON Sale
FOR EACH ROW
EXECUTE FUNCTION set_selling_price();
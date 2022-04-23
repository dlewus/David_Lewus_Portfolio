CREATE TABLE store (id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity_sold INTEGER, inventory INTEGER);

INSERT INTO store VALUES (1, "Garlic", 0.99, 100, 20);
INSERT INTO store VALUES (2, "Onion", 1.29, 200, 100);
INSERT INTO store VALUES (3, "Potato", 0.79, 200, 50);
INSERT INTO store VALUES (4, "Butternut Squash", 1.88, 20, 10);
INSERT INTO store VALUES (5, "Cucumber", 0.99, 30, 5);
INSERT INTO store VALUES (6, "Tomato", 0.59, 100, 15);
INSERT INTO store VALUES (7, "Strawberry", 2.99, 20, 5);
INSERT INTO store VALUES (8, "Grapes", 2.99, 30, 0);
INSERT INTO store VALUES (9, "Apple", 1.29, 50, 20);
INSERT INTO store VALUES (10, "Banana", 0.69, 300, 50);
INSERT INTO store VALUES (11, "Lettuce", 0.99, 50, 20);
INSERT INTO store VALUES (12, "Carrot", 1.99, 10, 100);
INSERT INTO store VALUES (13, "Broccoli", 2.19, 100, 10);
INSERT INTO store VALUES (14, "Bell Pepper", 2.99, 10, 20);
INSERT INTO store VALUES (15, "Watermelon", 6.99, 10, 0);

SELECT * FROM store ORDER BY price;
SELECT name, (price * quantity_sold) FROM store;
SELECT SUM(price*quantity_sold) FROM store;
SELECT name, MAX(price*quantity_sold) FROM store;


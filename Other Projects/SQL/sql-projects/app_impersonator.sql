/* What does the app's SQL look like? */

CREATE TABLE Players
(id INTEGER PRIMARY KEY,
name TEXT,
score INTEGER);

INSERT INTO Players (name, score) VALUES ("Jeff", 100);
INSERT INTO Players (name, score) VALUES ("Philip", 82);
INSERT INTO Players (name, score) VALUES ("Tommy", 68);

SELECT * FROM Players;

ALTER TABLE Players ADD real_gamer TEXT default "True";

UPDATE Players SET real_gamer = "False" WHERE name = "Philip";

SELECT * FROM Players;

DELETE FROM Players WHERE real_gamer = "False";

SELECT * FROM Players;

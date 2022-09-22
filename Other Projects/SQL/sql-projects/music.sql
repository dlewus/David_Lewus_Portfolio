/* Create table about the people and what they do here */
CREATE TABLE songs
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id INTEGER,
    song TEXT);

INSERT INTO songs (artist_id, song) VALUES (1, "Often");
INSERT INTO songs (artist_id, song) VALUES (1, "The Hills");
INSERT INTO songs (artist_id, song) VALUES (2, "Best Part");
INSERT INTO songs (artist_id, song) VALUES (2, "ENTROPY");
INSERT INTO songs (artist_id, song) VALUES (3, "Marvin's Room");
INSERT INTO songs (artist_id, song) VALUES (4, "War Pigs");
INSERT INTO songs (artist_id, song) VALUES (5, "Good Times Bad Times");
INSERT INTO songs (artist_id, song) VALUES (5, "Whole Lotta Love");
INSERT INTO songs (artist_id, song) VALUES (6, "Thunderstruck");

CREATE TABLE genre
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist TEXT,
    genre TEXT);

INSERT INTO genre (artist, genre) VALUES ("The Weeknd", "R&B");
INSERT INTO genre (artist, genre) VALUES ("Daniel Ceaser", "R&B");
INSERT INTO genre (artist, genre) VALUES ("Drake", "R&B");
INSERT INTO genre (artist, genre) VALUES ("Black Sabbath", "Rock");
INSERT INTO genre (artist, genre) VALUES ("Led Zeppelin", "Rock");
INSERT INTO genre (artist, genre) VALUES ("ACDC", "Rock");

/* Show Artist for each Song */
SELECT genre.artist, songs.song
    FROM genre
    JOIN songs
    ON genre.id = songs.artist_id;

/* Show only R&B Songs */
SELECT genre.artist, songs.song
    FROM genre
    JOIN songs
    ON genre.id = songs.artist_id
    WHERE genre.genre = "R&B";

/* Show only Rock Songs */
SELECT genre.artist, songs.song
    FROM genre
    JOIN songs
    ON genre.id = songs.artist_id
    WHERE genre.genre = "Rock";


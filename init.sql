-- Create a new database
CREATE DATABASE luminary;

-- Connect to the database
\c luminary;

-- Create a table
CREATE TABLE mytable (
    id serial PRIMARY KEY,
    name varchar(50)
);

-- Insert some initial data
INSERT INTO mytable (name) VALUES ('John Doe');
INSERT INTO mytable (name) VALUES ('Jane Smith');

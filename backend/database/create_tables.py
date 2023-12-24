import psycopg2
from decouple import config

def create_connection():
    connection = psycopg2.connect(
        host=config("DB_HOST"),
        user=config("DB_USER"),
        password=config("DB_PASSWORD"),
        database=config("DB_DATABASE")
    )
    return connection

def create_user_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "user" (
        user_id SERIAL,
        username TEXT NOT NULL,
        password VARCHAR NOT NULL,
        email TEXT NOT NULL PRIMARY KEY,
        phone TEXT NOT NULL,
        address TEXT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

def create_locker_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locker (
        locker_id SERIAL PRIMARY KEY,
        address TEXT NOT NULL,
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

def create_locker_status_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locker_status (
        locker_status_id SERIAL PRIMARY KEY,
        locker_id INT NOT NULL,
        occupied BOOLEAN DEFAULT FALSE NOT NULL,
        FOREIGN KEY (locker_id) REFERENCES locker (locker_id)
    )
    """)
    connection.commit()
    connection.close()

create_user_table()
create_locker_table()
create_locker_status_table()
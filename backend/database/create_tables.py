import psycopg2
from decouple import config

def create_connection():
    connection = psycopg2.connect(
        host="localhost",
        user="postgres",
        password=config("PASSWORD_SQL"),
        database="parcel-locker"
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

create_user_table()
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.ext.declarative import declarative_base
from decouple import config
import psycopg2

# Import all the models in the database

URL_DATABASE = config("DATABASE_URL")

connect_args = {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 5
}

engine = create_engine(URL_DATABASE, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def execute_sql_file(file_path: str):
    try:
        connection = psycopg2.connect(URL_DATABASE)
        cursor = connection.cursor()
        # Read the SQL file
        with open(file_path, 'r') as sql_file:
            sql_script = sql_file.read()
        
        # Execute the script
        cursor.execute(sql_script)
        connection.commit()

        print("SQL script executed successfully.")
    except Exception as error:
        print(f"Error executing SQL script: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
from decouple import config
# Import all the models in the database

URL_DATABASE = config("DATABASE_URL")
REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT")

from decouple import config

SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")
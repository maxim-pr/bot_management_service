from environs import Env


env = Env()
env.read_env()

SECRET_KEY = env.str("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DB_URL = env.str("DB_URL")
DB_NAME = env.str("DB_NAME")
DB_USERS_COLLECTION_NAME = env.str("DB_USERS_COLLECTION_NAME")
IP = env.str("IP")
PORT = env.int("PORT")
from environs import Env


env = Env()
env.read_env()

SECRET_KEY = env.str("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

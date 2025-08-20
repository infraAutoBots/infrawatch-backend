import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
SECRET_KEY =  os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

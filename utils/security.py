from passlib.context import CryptContext

# 初始化密码加密器（必须写）
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 密码加密
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 密码校验（唯一一个，不要重复）
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
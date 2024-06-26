import datetime
import jwt
from dotenv import load_dotenv
import os
import re

load_dotenv()


def create_access_token():
    subject = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_delta = datetime.timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    expire = now + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt.decode("utf-8")


def create_refresh_token(subject: str) -> str:
    refresh_token_expiration_minutes = int(os.getenv("REFRESH_TOKEN_EXPIRATION"))
    refresh_token_expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=refresh_token_expiration_minutes)
    payload = {
        "sub": subject,
        "exp": refresh_token_expiration,
        "iat": datetime.datetime.now(datetime.timezone.utc)
    }

    refresh_token = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")

    return refresh_token.decode("utf-8")


def is_token_expired(access_token: str) -> bool:
    try:
        decoded_token = jwt.decode(access_token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        expiration_time = decoded_token.get("exp")
        expiration_time = datetime.datetime.fromtimestamp(expiration_time, datetime.timezone.utc)
        current_time = datetime.datetime.now(datetime.timezone.utc)
        if expiration_time is not None and expiration_time < current_time:
            return True
        else:
            return False
    except jwt.ExpiredSignatureError:
        return True


def handle_username(username):
    username = username.replace(" ", "").replace("\n", "").replace("\r", "")
    username = username.replace("，", ",")
    return username.split(",")


def is_valid_id(id_number):
    # 长度检查
    if len(id_number) != 18:
        return False

    # 格式检查
    if not re.match(r'^\d{17}[\dXx]$', id_number):
        return False

    # 校验码检查
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    sum_ = 0
    for i in range(17):
        sum_ += int(id_number[i]) * weights[i]

    index = sum_ % 11
    if check_codes[index].upper() != id_number[-1].upper():
        return False

    return True


def is_valid_date(date_string, format='%Y%m%d'):
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date_string, format)
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return None

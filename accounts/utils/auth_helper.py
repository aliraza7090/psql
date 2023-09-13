import jwt
from datetime import datetime


def get_token_expiry_remaining_minutes(token):
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    
    expiry_timestamp = decoded_token.get("exp")
    expiry_datetime = datetime.fromtimestamp(expiry_timestamp)

    current_datetime = datetime.now()

    time_remaining = expiry_datetime - current_datetime

    minutes_remaining = int(time_remaining.total_seconds() / 60)
    
    print(minutes_remaining)

    return minutes_remaining


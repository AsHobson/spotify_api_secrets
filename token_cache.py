import json
import time
from pathlib import Path

#TOKEN_FILE = Path("token_cache.json")
token_file = Path('user_token.json')


def load_cached_token():
    if not token_file.exists():
        print("token doesn't exist")
        return None
    
    token_data = json.loads(token_file.read_text())

    return token_data


def save_token(token_info):
    data = {
        "access_token": token_info['access_token'],
        "refresh_token": token_info['refresh_token'],
        "expires_at": token_info['expires_at'] - 60
    }
    token_file.write_text(json.dumps(data))
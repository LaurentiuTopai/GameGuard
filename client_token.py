import os
import secrets

def load_or_create_token(path):

    if os.path.exists(path):
        try:
            with open(path,"rb") as f:
                return f.read().decode("utf-8")
        except Exception:
            
            pass
    
    token = secrets.token_hex(32)
    with open(path,"wb") as f:
        f.write(token.encode("utf-8"))
    return token
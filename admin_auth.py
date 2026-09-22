import os
import json
import hashlib
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRED_FILE = os.path.join(BASE_DIR, "data", "admin_credentials.json")
ANN_FILE = os.path.join(BASE_DIR, "data", "announcements.json")
COUNTER_FILE = os.path.join(BASE_DIR, "data", "counter.json")


def _hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{h.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt, h = stored.split(":", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return check.hex() == h


def init_credentials():
    if not os.path.exists(CRED_FILE):
        creds = {
            "username": "admin",
            "password": _hash_password("X9k#2mP$7vLq!5nR")
        }
        os.makedirs(os.path.dirname(CRED_FILE), exist_ok=True)
        with open(CRED_FILE, "w") as f:
            json.dump(creds, f, indent=2)


def check_credentials(username: str, password: str) -> bool:
    if not os.path.exists(CRED_FILE):
        init_credentials()
    with open(CRED_FILE, "r") as f:
        creds = json.load(f)
    return creds["username"] == username and _verify_password(password, creds["password"])


def change_password(new_password: str):
    if not os.path.exists(CRED_FILE):
        init_credentials()
    with open(CRED_FILE, "r") as f:
        creds = json.load(f)
    creds["password"] = _hash_password(new_password)
    with open(CRED_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def load_announcements() -> list:
    if not os.path.exists(ANN_FILE):
        return []
    with open(ANN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_announcements(data: list):
    os.makedirs(os.path.dirname(ANN_FILE), exist_ok=True)
    with open(ANN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_announcement(text: str, color: str = "green") -> dict:
    anns = load_announcements()
    item = {
        "id": len(anns) + 1,
        "text": text,
        "color": color,
        "active": True,
        "created_at": datetime.now().isoformat()
    }
    anns.append(item)
    save_announcements(anns)
    return item


def delete_announcement(ann_id: int):
    anns = load_announcements()
    anns = [a for a in anns if a["id"] != ann_id]
    save_announcements(anns)


def load_counter() -> dict:
    if not os.path.exists(COUNTER_FILE):
        return {"enabled": False, "count": 0, "style": "standard"}
    with open(COUNTER_FILE, "r") as f:
        return json.load(f)


def save_counter(data: dict):
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f, indent=2)


def increment_counter():
    c = load_counter()
    c["count"] = c.get("count", 0) + 1
    save_counter(c)


from datetime import datetime

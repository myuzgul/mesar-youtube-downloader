import os
import sys
import json
import hashlib
import hmac
import time
from typing import Tuple, Dict, Any, Optional

if os.name == 'nt':
    import winreg

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APPDATA_DIR = os.getenv('APPDATA', os.path.expanduser('~'))
APP_DATA_FOLDER = os.path.join(APPDATA_DIR, 'MediaDownloaderPro')
LICENSE_FILE = os.path.join(APP_DATA_FOLDER, 'license.dat')

# Master secret used for signing valid license keys and credit records
SECRET_SALT = "MDP_PRO_SECRET_KEY_SALT_2026_HWID_SECURITY"
MAX_FREE_CREDITS = 10

def get_hwid() -> str:
    """Generates a unique Hardware Fingerprint (HWID)."""
    raw_ids = []
    if os.name == 'nt':
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            guid, _ = winreg.QueryValueEx(reg_key, "MachineGuid")
            winreg.CloseKey(reg_key)
            raw_ids.append(str(guid))
        except Exception:
            pass

    user_info = f"{os.getenv('COMPUTERNAME', '')}-{os.getenv('USERNAME', '')}"
    raw_ids.append(user_info)
    
    combined = "|".join(raw_ids).encode('utf-8')
    digest = hashlib.sha256(combined).hexdigest().upper()
    return f"HWID-{digest[0:4]}-{digest[4:8]}-{digest[8:12]}"

MESAR_SECRET_SALT = "MESAR_YOUTUBE_DOWNLOADER_2026_MASTER_SECRET_KEY_HWID"

def calculate_key_signature(prefix: str, rand_part: str, salt: str = SECRET_SALT) -> str:
    msg = f"{prefix}:{rand_part}".encode('utf-8')
    sig = hmac.new(salt.encode('utf-8'), msg, hashlib.sha256).hexdigest().upper()
    return sig[:8]

def generate_license_key(user_prefix: str = "PRO") -> str:
    import random
    import string
    rand_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    sig = calculate_key_signature(user_prefix, rand_chars, SECRET_SALT)
    return f"MDP-{user_prefix}-{rand_chars}-{sig[:4]}-{sig[4:8]}"

def verify_license_key(key: str) -> bool:
    if not key or not isinstance(key, str):
        return False
        
    parts = key.strip().upper().split('-')
    if len(parts) != 5:
        return False
        
    app_tag = parts[0]
    if app_tag == "MDP":
        salt = SECRET_SALT
    elif app_tag == "MESAR":
        salt = MESAR_SECRET_SALT
    else:
        return False

    prefix = parts[1]
    rand_part = parts[2]
    provided_sig = parts[3] + parts[4]
    
    expected_sig = calculate_key_signature(prefix, rand_part, salt)
    return hmac.compare_digest(provided_sig, expected_sig)

def _load_data() -> Dict[str, Any]:
    current_hwid = get_hwid()
    if not os.path.exists(LICENSE_FILE):
        return {
            "key": None,
            "hwid": current_hwid,
            "free_credits_used": 0,
            "activated": False
        }
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        key = data.get("key")
        saved_hwid = data.get("hwid", current_hwid)
        credits_used = data.get("free_credits_used", 0)
        saved_sig = data.get("token_sig")
        
        # Verify token signature integrity
        expected_sig = hmac.new(SECRET_SALT.encode('utf-8'), f"{key}:{saved_hwid}:{credits_used}".encode('utf-8'), hashlib.sha256).hexdigest()
        
        is_valid_key = verify_license_key(key) if key else False
        is_same_hwid = (saved_hwid == current_hwid)
        is_valid_sig = hmac.compare_digest(saved_sig, expected_sig) if saved_sig else False

        activated = is_valid_key and is_same_hwid and is_valid_sig

        return {
            "key": key if activated else None,
            "hwid": current_hwid,
            "free_credits_used": credits_used if is_same_hwid else 0,
            "activated": activated
        }
    except Exception:
        return {
            "key": None,
            "hwid": current_hwid,
            "free_credits_used": 0,
            "activated": False
        }

def _save_data(key: Optional[str], credits_used: int) -> None:
    os.makedirs(APP_DATA_FOLDER, exist_ok=True)
    hwid = get_hwid()
    sig_payload = f"{key}:{hwid}:{credits_used}".encode('utf-8')
    sig = hmac.new(SECRET_SALT.encode('utf-8'), sig_payload, hashlib.sha256).hexdigest()
    
    payload = {
        "key": key,
        "hwid": hwid,
        "free_credits_used": credits_used,
        "activated_at": int(time.time()),
        "token_sig": sig
    }
    
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def is_activated() -> Tuple[bool, Optional[str], str]:
    data = _load_data()
    return data["activated"], data["key"], data["hwid"]

def get_credit_info() -> Dict[str, Any]:
    data = _load_data()
    activated = data["activated"]
    used = data["free_credits_used"]
    remaining = 0 if activated else max(0, MAX_FREE_CREDITS - used)
    
    return {
        "activated": activated,
        "key": data["key"],
        "hwid": data["hwid"],
        "free_credits_used": used,
        "free_credits_remaining": remaining if not activated else 99999,
        "max_credits": MAX_FREE_CREDITS
    }

def consume_credit() -> Tuple[bool, int]:
    """Decrements one free credit if not activated. Returns (allowed, remaining)."""
    data = _load_data()
    if data["activated"]:
        return True, 99999
        
    used = data["free_credits_used"]
    if used >= MAX_FREE_CREDITS:
        return False, 0
        
    new_used = used + 1
    _save_data(data["key"], new_used)
    remaining = MAX_FREE_CREDITS - new_used
    return True, remaining

KEYS_HISTORY_FILE = os.path.join(APP_DATA_FOLDER, 'generated_keys.json')

def get_all_generated_keys() -> list:
    if not os.path.exists(KEYS_HISTORY_FILE):
        return []
    try:
        with open(KEYS_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def generate_bulk_keys(count: int = 1, prefix: str = "PRO", note: str = "") -> list:
    count = max(1, min(count, 100)) # Limit 1-100 keys per request
    clean_prefix = prefix.strip().upper() if prefix else "PRO"
    
    history = get_all_generated_keys()
    new_keys = []
    
    for _ in range(count):
        key = generate_license_key(clean_prefix)
        entry = {
            "key": key,
            "prefix": clean_prefix,
            "note": note,
            "created_at": int(time.time()),
            "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        new_keys.append(entry)
        history.insert(0, entry)
        
    os.makedirs(APP_DATA_FOLDER, exist_ok=True)
    try:
        with open(KEYS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print("Lisans geçmişi kaydetme hatası:", e)
        
    return new_keys

def activate(key: str) -> Tuple[bool, str]:
    clean_key = key.strip().upper()
    if not verify_license_key(clean_key):
        return False, "Geçersiz Lisans Anahtarı! Lütfen kontrol edip tekrar deneyin."
        
    data = _load_data()
    _save_data(clean_key, data["free_credits_used"])
    return True, "Lisans başarıyla etkinleştirildi! Sınırsız indirme aktif."

if __name__ == "__main__":
    hwid = get_hwid()
    print(f"Current System HWID: {hwid}")
    sample_key = generate_license_key("PRO")
    print(f"Generated Test Key: {sample_key}")
    info = get_credit_info()
    print(f"Credit Info: {info}")

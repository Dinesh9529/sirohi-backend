import random
import time

# Temporary in-memory OTP store
otp_store = {}  # Format: { phone_number: {"otp": "1234", "timestamp": 1723728827} }

OTP_EXPIRY_SECONDS = 300  # 5 minutes

def generate_otp():
    return str(random.randint(1000, 9999))

def save_otp(phone, otp):
    otp_store[phone] = {
        "otp": otp,
        "timestamp": time.time()
    }

def verify_otp(phone, user_otp):
    record = otp_store.get(phone)
    if not record:
        return False

    if time.time() - record["timestamp"] > OTP_EXPIRY_SECONDS:
        del otp_store[phone]
        return False

    if record["otp"] == user_otp:
        del otp_store[phone]  # Optional: remove used OTP
        return True

    return False

def save_user(data):
    # Stub: In real setup, you might save to a database or Firestore
    print(f"User registered: {data['phone']} - {data.get('name', 'No Name')}")

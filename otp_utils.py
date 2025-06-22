import json, random, time, os

def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp(phone, otp):
    os.makedirs("data", exist_ok=True)
    with open("data/otps.json", "w") as f:
        json.dump({phone: {"otp": otp, "time": time.time()}}, f)

def verify_otp(phone, entered):
    try:
        with open("data/otps.json") as f:
            data = json.load(f)
            return data.get(phone, {}).get("otp") == entered and time.time() - data[phone]["time"] < 300
    except:
        return False

def save_user(user_data):
    os.makedirs("data", exist_ok=True)
    file = "data/users.json"
    try:
        users = json.load(open(file))
    except:
        users = []
    users.append(user_data)
    with open(file, "w") as f:
        json.dump(users, f, indent=2)

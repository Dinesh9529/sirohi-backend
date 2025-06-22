from flask import Flask, request, jsonify
from otp_utils import generate_otp, save_otp, verify_otp, save_user

app = Flask(__name__)

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    phone = data.get("phone", "")
    if len(phone) != 10 or not phone.isdigit():
        return jsonify(success=False, message="Invalid phone number")
    otp = generate_otp()
    save_otp(phone, otp)
    return jsonify(success=True, message="OTP sent", otp=otp)  # Mask in real prod

@app.route("/verify-otp", methods=["POST"])
def verify():
    data = request.json
    if verify_otp(data.get("phone"), data.get("otp")):
        return jsonify(success=True, message="OTP verified")
    return jsonify(success=False, message="Invalid or expired OTP")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if not verify_otp(data.get("phone"), data.get("otp")):
        return jsonify(success=False, message="OTP verification failed")
    save_user(data)
    return jsonify(success=True, message="User registered")

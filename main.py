from flask import Flask, request, jsonify
from otp_utils import generate_otp, save_otp, verify_otp, save_user
import requests, urllib.parse
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()  # Load environment variables from .env file

# 📤 Send SMS using SMSINDIAHUB
def send_sms(phone, otp):
    base_url = "http://cloud.smsindiahub.in/vendorsms/pushsms.aspx"
    params = {
        "APIKey": os.getenv("SMS_API_KEY"),
        "msisdn": f"91{phone}",
        "sid": os.getenv("SENDER_ID", "SMSHUB"),
        "msg": f"Dear user, your OTP is {otp}",
        "fl": "0",
        "gwid": "2"
    }
    final_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = requests.get(final_url)
    return response.text

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    phone = data.get("phone", "")
    if len(phone) != 10 or not phone.isdigit():
        return jsonify(success=False, message="Invalid phone number")

    otp = generate_otp()
    save_otp(phone, otp)

    sms_status = send_sms(phone, otp)

    return jsonify(success=True, message="OTP भेजा गया है!", sms_status=sms_response.text)
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

if __name__ == "__main__":
    app.run(debug=True)

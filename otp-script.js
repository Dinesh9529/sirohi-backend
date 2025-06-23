const BACKEND_URL = "https://sirohi-backend.onrender.com"; // Replace with actual Render URL

console.log("Send OTP called");
async function sendOTP() {
  const phone = document.getElementById("phone").value.trim();
  if (!/^\d{10}$/.test(phone)) {
    alert("Please enter a valid 10-digit number");
    return;
  }

  const res = await fetch(`${BACKEND_URL}/send-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone })
  });

  const data = await res.json();
  alert(data.message);
}

async function verifyOTP() {
  const phone = document.getElementById("phone").value.trim();
  const otp = document.getElementById("otp").value.trim();

  const res = await fetch(`${BACKEND_URL}/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp })
  });

  const data = await res.json();
  alert(data.message);
}

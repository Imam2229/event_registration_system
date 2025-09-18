from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_mail import Mail, Message
from fpdf import FPDF
import qrcode
from io import BytesIO
from PIL import Image
import base64
import os

# ---------------- Flask App ----------------
app = Flask(__name__)

# ---------------- MongoDB Setup ----------------
# Change "event_registration_db" & "registrations" if needed
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["event_registration_db"]
registrations = db["registrations"]

# ---------------- Flask-Mail Setup ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")   # your Gmail
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")   # app password
mail = Mail(app)

# ---------------- Home ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Event Registration API is Live on Vercel ✅"})

# ---------------- Register Endpoint ----------------
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        name = data.get("name")
        email = data.get("email")
        event = data.get("event")

        if not (name and email and event):
            return jsonify({"error": "Missing fields"}), 400

        # Save to MongoDB
        reg_data = {"name": name, "email": email, "event": event}
        registrations.insert_one(reg_data)

        # Generate QR code
        qr_img = qrcode.make(f"{name} - {event}")
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # Generate Ticket (PDF)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="Event Ticket", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
        pdf.cell(200, 10, txt=f"Event: {event}", ln=True)

        # Save QR to temp and add to PDF
        qr_path = "/tmp/qr.png"
        qr_img.save(qr_path)
        pdf.image(qr_path, x=80, y=60, w=50, h=50)

        pdf_path = "/tmp/ticket.pdf"
        pdf.output(pdf_path)

        # Send Email with Ticket
        msg = Message("Your Event Ticket", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = f"Hello {name},\n\nThank you for registering for {event}!"
        with open(pdf_path, "rb") as f:
            msg.attach("ticket.pdf", "application/pdf", f.read())
        mail.send(msg)

        return jsonify({"message": "Registration successful", "qr_code": qr_b64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- Vercel Entry ----------------
# Vercel looks for `app`
if __name__ == "__main__":
    app.run()

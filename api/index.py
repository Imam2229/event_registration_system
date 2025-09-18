from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_mail import Mail, Message
from fpdf import FPDF
import qrcode
import io
from werkzeug.security import generate_password_hash, check_password_hash
import base64

app = Flask(__name__)

# ----------------- MongoDB Setup -----------------
client = MongoClient(
    "mongodb+srv://shahnawazimam53_db_user:Imam1234@cluster0.ccc3bdn.mongodb.net/?retryWrites=true&w=majority"
)
db = client["event_registration_db"]
users = db["users"]

# ----------------- Mail Config -----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "shahbazimam0111@gmail.com"
app.config["MAIL_PASSWORD"] = "igtpbkwrjovssigs"  # Gmail App Password
app.config["MAIL_DEFAULT_SENDER"] = "shahbazimam0111@gmail.com"

mail = Mail(app)


# ----------------- Routes -----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Event Registration API is Live on Vercel ✅"})


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Name, Email & Password required"}), 400

    # check if user already exists
    if users.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    # Hash password
    hashed_password = generate_password_hash(password)

    # save in DB
    users.insert_one(
        {"name": name, "email": email, "password": hashed_password}
    )

    # Generate Ticket (PDF + QR)
    ticket_pdf, ticket_bytes = generate_ticket(name, email)

    # Send mail with ticket
    msg = Message("🎟️ Event Registration Successful", recipients=[email])
    msg.body = f"Hello {name},\n\nYou have successfully registered for the event!"
    msg.attach("ticket.pdf", "application/pdf", ticket_bytes)
    mail.send(msg)

    return jsonify({"message": "User registered & ticket sent on email ✅"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email & Password required"}), 400

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": f"Welcome back {user['name']} ✅"})


# ----------------- Ticket Generator -----------------
def generate_ticket(name, email):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Event Ticket", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {email}", ln=True)

    # QR Code
    qr_data = f"Name: {name}, Email: {email}"
    qr = qrcode.make(qr_data)
    qr_io = io.BytesIO()
    qr.save(qr_io, "PNG")
    qr_io.seek(0)

    qr_filename = "qr.png"
    with open(qr_filename, "wb") as f:
        f.write(qr_io.read())

    pdf.image(qr_filename, x=80, y=60, w=50, h=50)

    # save PDF in memory
    pdf_bytes = pdf.output(dest="S").encode("latin1")

    return pdf, pdf_bytes


# ----------------- Vercel Handler -----------------
# Important: For Vercel, keep app as "app"
# No need for app.run()

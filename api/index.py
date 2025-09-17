from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from pymongo import MongoClient
from flask_mail import Mail, Message
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from io import BytesIO
import os
import qrcode

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ---------------- MongoDB Setup ----------------
client = MongoClient(
    "mongodb+srv://shahnawazimam53_db_user:Imam1234@cluster0.ccc3bdn.mongodb.net/?retryWrites=true&w=majority"
)
db = client["event_registration_db"]
users_collection = db["users"]
registrations = db["registrations"]

# ---------------- SMTP Email Setup ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "shahbazimam0111@gmail.com"
app.config["MAIL_PASSWORD"] = "igtpbkwrjovssigs"  # App password
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]
mail = Mail(app)

# ---------------- Routes ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- User Signup ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        age = request.form["age"]
        password = request.form["password"]

        if users_collection.find_one({"email": email}):
            return render_template("signup.html", success=False, message="Email already registered!")

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            "name": name,
            "email": email,
            "age": age,
            "password": hashed_password
        })

        flash("✅ Account created successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# ---------------- User Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_collection.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", success=False, message="❌ Invalid email or password!")

    return render_template("login.html")

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user_name=session["user_name"])

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("✅ You have been logged out.", "info")
    return redirect(url_for("login"))

# ---------------- Event Registration ----------------
@app.route("/register", methods=["GET", "POST"])
def register_event():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        data = {
            "event_name": request.form["event_name"],
            "user_name": request.form["user_name"],
            "organizers": request.form["organizers"],
            "event_type": request.form.get("event_type", "General"),
            "email": request.form["email"],
            "event_date": request.form["event_date"],
            "event_time": request.form["event_time"],
            "participants": int(request.form["participants"]),
            "event_address": request.form["event_address"],
            "ticket_price": request.form["ticket_price"],
            "user_email": session["user_email"]
        }

        try:
            result = registrations.insert_one(data)
            event_id = str(result.inserted_id)

            # Email Confirmation
            try:
                msg = Message(
                    subject=f"Registration Successful for {data['event_name']}",
                    recipients=[data['email']]
                )
                msg.body = f"""
Hello {data['user_name']},

Your registration for the event "{data['event_name']}" is successful.

Event Details:
Organizers: {data['organizers']}
Type: {data['event_type']}
Date & Time: {data['event_date']} at {data['event_time']}
Participants: {data['participants']}
Address: {data['event_address']}
Ticket Price: ₹{data['ticket_price']}

You can view and download your tickets here: http://127.0.0.1:5000/ticket/{event_id}

Thank you for registering!
"""
                mail.send(msg)
            except Exception as e:
                print(f"⚠️ Email failed to send: {str(e)}")

            return render_template("success.html", event_id=event_id)

        except Exception as e:
            return render_template("registration.html", success=False, message=f"❌ Registration Failed: {str(e)}")

    return render_template("registration.html")

# ---------------- User's Events ----------------
@app.route("/my_events")
def my_events():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user_events = list(registrations.find({"user_email": session["user_email"]}))
    return render_template("my_events.html", events=user_events)

# ---------------- Ticket Generation ----------------
@app.route("/ticket/<ticket_id>")
def ticket(ticket_id):
    try:
        event = registrations.find_one({"_id": ObjectId(ticket_id)})
        if not event:
            return "❌ Ticket not found!"

        tickets = []
        for i in range(1, int(event["participants"]) + 1):
            tickets.append({
                "ticket_number": f"{ticket_id}-{i:03d}",
                "event": event["event_name"],
                "organizers": event["organizers"],
                "event_type": event.get("event_type", "General"),
                "date": event["event_date"],
                "time": event["event_time"],
                "address": event["event_address"],
                "price": event["ticket_price"],
                "participant_no": i
            })

        return render_template("ticket.html", event=event, tickets=tickets)

    except Exception as e:
        return f"⚠️ Error loading ticket: {str(e)}"

# ---------------- Download Tickets as PDF with QR ----------------
@app.route("/download_ticket/<ticket_id>")
def download_ticket(ticket_id):
    try:
        event = registrations.find_one({"_id": ObjectId(ticket_id)})
        if not event:
            return "❌ Ticket not found!"

        tickets = []
        for i in range(1, int(event["participants"]) + 1):
            tickets.append({
                "ticket_number": f"{ticket_id}-{i:03d}",
                "event": event["event_name"],
                "organizers": event["organizers"],
                "event_type": event.get("event_type", "General"),
                "date": event["event_date"],
                "time": event["event_time"],
                "address": event["event_address"],
                "price": event["ticket_price"],
                "participant_no": i
            })

        # Create PDF
        pdf = FPDF(format='A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        font_path = os.path.join(os.path.dirname(__file__), "dejavu-sans", "DejaVuSans.ttf")
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 14)

        for t in tickets:
            pdf.add_page()
            pdf.set_text_color(0, 0, 128)
            pdf.cell(0, 10, f"🎟 Ticket Number: {t['ticket_number']}", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, f"Event: {t['event']}", ln=True)
            pdf.cell(0, 10, f"Organizers: {t['organizers']}", ln=True)
            pdf.cell(0, 10, f"Type: {t['event_type']}", ln=True)
            pdf.cell(0, 10, f"Date: {t['date']}", ln=True)
            pdf.cell(0, 10, f"Time: {t['time']}", ln=True)
            pdf.cell(0, 10, f"Address: {t['address']}", ln=True)
            pdf.cell(0, 10, f"Price: ₹{t['price']}", ln=True)
            pdf.cell(0, 10, f"Participant No: {t['participant_no']}", ln=True)

            # Generate QR code for ticket
            qr_data = f"Ticket: {t['ticket_number']}\nEvent: {t['event']}\nParticipant: {t['participant_no']}"
            qr = qrcode.QRCode(box_size=2, border=1)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_path = BytesIO()
            qr_img.save(qr_path, format="PNG")
            qr_path.seek(0)
            pdf.image(qr_path, x=160, y=10, w=40, h=40)

        # Convert PDF to BytesIO
        pdf_io = BytesIO()
        pdf.output(pdf_io)
        pdf_io.seek(0)

        return send_file(
            pdf_io,
            as_attachment=True,
            download_name=f"tickets_{ticket_id}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return f"⚠️ Error generating PDF: {str(e)}"

# ---------------- Admin (All Events) ----------------
@app.route("/admin")
def admin():
    all_registrations = list(registrations.find())
    return render_template("admin.html", registrations=all_registrations)

# ---------------- Run Flask ----------------
if __name__ == "__main__":
    app.run(debug=True)

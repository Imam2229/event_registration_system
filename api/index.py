from flask import Flask, render_template, request
from pymongo import MongoClient
from flask_mail import Mail, Message

app = Flask(__name__)

# ---------------- MongoDB Atlas Setup ----------------
client = MongoClient("mongodb+srv://shahnawazimam53_db_user:Imam1234@cluster0.ccc3bdn.mongodb.net/?retryWrites=true&w=majority")

# Database and collection
db = client["event_registration_db"]
registrations = db["registrations"]

# ---------------- SMTP Email Setup ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "shahbazimam0111@gmail.com"      # Apna Gmail
app.config["MAIL_PASSWORD"] = "igtpbkwrjovssigs"               # App password
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

mail = Mail(app)

# ---------------- Routes ----------------
@app.route("/")
def home():
    return render_template("index.html")  # Home page

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = {
            "event_name": request.form["event_name"],
            "user_name": request.form["user_name"],
            "organizers": request.form["organizers"],
            "email": request.form["email"],
            "event_date": request.form["event_date"],
            "event_time": request.form["event_time"],
            "participants": request.form["participants"],
            "event_address": request.form["event_address"],
            "ticket_price": request.form["ticket_price"]
        }

        try:
            # --- Save to MongoDB ---
            registrations.insert_one(data)

            # --- Send confirmation email ---
            msg = Message(
                subject=f"Registration Successful for {data['event_name']}",
                recipients=[data['email']]
            )
            msg.body = f"""
Hello {data['user_name']},

Your registration for the event "{data['event_name']}" is successful.

Event Details:
Organizers: {data['organizers']}
Date & Time: {data['event_date']} at {data['event_time']}
Participants: {data['participants']}
Address: {data['event_address']}
Ticket Price: {data['ticket_price']}

Thank you for registering!
"""
            mail.send(msg)

            return render_template("registration.html", success=True, message="✅ Registration Successful! Email sent.")
        except Exception as e:
            return render_template("registration.html", success=False, message=f"❌ Registration Failed: {str(e)}")

    return render_template("registration.html")

@app.route("/admin")
def admin():
    all_registrations = list(registrations.find())
    return render_template("admin.html", registrations=all_registrations)

# 🔹 New Route for Event List
@app.route("/eventList")
def event_list():
    try:
        all_events = list(registrations.find())
        return render_template("eventList.html", events=all_events)
    except Exception as e:
        return f"Error loading events: {str(e)}"

# ---------------- Run Flask ----------------
if __name__ == "__main__":
    app.run(debug=True)

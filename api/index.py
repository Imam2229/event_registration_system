from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# ---------------- MongoDB Atlas Setup ----------------
client = MongoClient("mongodb+srv://shahnawazimam53_db_user:Imam1234@cluster0.ccc3bdn.mongodb.net/?retryWrites=true&w=majority")

# Database and collection
db = client["event_registration_db"]   # Atlas me yeh DB ban jayega
registrations = db["registrations"]    # Collection ka naam

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
            registrations.insert_one(data)
            return render_template("registration.html", success=True, message="✅ Registration Successful!")
        except Exception as e:
            return render_template("registration.html", success=False, message=f"❌ Registration Failed: {str(e)}")
    
    return render_template("registration.html")

@app.route("/admin")
def admin():
    all_registrations = list(registrations.find())
    return render_template("admin.html", registrations=all_registrations)

# ---------------- Run Flask ----------------
if __name__ == "__main__":
    app.run(debug=True)
